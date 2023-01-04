from __future__ import print_function
import os.path
import profile
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from pprint import pprint

import base64
import json
import time
import sys 

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
ATTACHMENT_PATH_PREFIX = os.environ.get('TMP_DIR','/data/out')

try:
    os.mkdir(ATTACHMENT_PATH_PREFIX)
except:
    pass 

DEFAULT_FILTER = os.environ.get('DEFAULT_MAIL_FILTER','NOT in:processed')

def str2bool(v):
  return str(v).lower() in ("yes", "true", "t", "1")

class GmailApp():

    @staticmethod
    def login(token_file,credentials_file='credentials.json'):
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        return GmailApp(token_file)

    def __init__(self,token_file='token.json'):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        if creds and creds.expired and creds.refresh_token:
            print(f"Token file:{token_file} expired, refreshing...")
            creds.refresh(Request())

        self.service = build('gmail', 'v1', credentials=creds)
        self.profile = self.service.users().getProfile(userId='me').execute()
        print(f"Logged in to gmail for user: {self.profile}")

    
    def get_emails(self,**kwargs):
        q=[DEFAULT_FILTER]
        if kwargs.get('from_',None):
            q.append('from: %s ' % kwargs.get('from_'))
        if kwargs.get('to',None):
            q.append('to: %s ' % kwargs.get('to',None))
        if kwargs.get('subject',None):
            q.append('subject: "%s" '  %  kwargs.get('subject'))
        if kwargs.get('label',None):
            q.append('label:%s' % kwargs['label'])
        if kwargs.get('after',None):
            q.append('after: %d' % int(kwargs['after']) )
        if kwargs.get('before',None):
            q.append('before: %d' % int(kwargs['before']) )
        if str2bool(kwargs.get('attachment',None)) :
            q.append('has:attachment ')
        
        q  = ' AND '.join(q)

        results = self.service.users().messages().list(userId='me',q=q ).execute()
        messages = results.get('messages',[])
        print(" EMAIL Filter: %s \n  Matched %d emails" % ( q, len(messages)  ) )
        
        emails = []
        for emailId in messages:
            emailId = emailId['id']
            email =  self.service.users().messages().get(userId='me',id=emailId).execute()
            emails.append(email)
            # pprint(email)
            # path = ATTACHMENT_PATH_PREFIX + emailId + '.json'
            # with open(path, 'w') as outfile:
            #     json.dump(email['payload'], outfile)
            try:
                os.mkdir(os.path.join(ATTACHMENT_PATH_PREFIX,email['id']))
            except:
                pass

            if kwargs.get('save_body',False):
                self.save_email_body(email)
        emails =  sorted(emails, key=lambda m: m['internalDate'] )
        return emails
    
    def save_email_body(self, email,mime_type='text/html'):
        emailId = email['id']
        path = os.path.join(ATTACHMENT_PATH_PREFIX , emailId , 'body.eml')

        try: 
            body = None
            if int(email['payload']['body']['size']):
                body = email['payload']['body']['data']
            else:
                parts = email['payload']['parts']
                for part in parts:
                    if part.get('parts',None):
                        parts += part['parts']
                        del part['parts']
                
                for part in parts:
                    if part['filename'] == '' and part['mimeType'] == mime_type:
                        body = part['body']['data']

            if body:
                body = body.replace('-/','+/')
                body = base64.urlsafe_b64decode(body.encode('UTF-8'))
                with open(path,'wb') as wf:
                    wf.write(body)

                print("Email body with type %s save at %s" % ( mime_type, path))
                return path
        except Exception as ex:
            print(ex)
            print("Error at %s:%s : %s " % (self.__class__.__name__, sys._getframe().f_code.co_name, ex) )
        

    def download_attachment(self,emailId,attachment):
        if 'data' in attachment['body']:
            data = attachment['body']['data']
        else:
            attResults  = self.service.users().messages().attachments() \
                            .get(userId='me', messageId=emailId,id=attachment['body']['attachmentId']) \
                            .execute()
            data=attResults['data']
        file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
        
        path = os.path.join(ATTACHMENT_PATH_PREFIX , emailId  , attachment['filename'])
        with open(path, 'wb') as f:
                f.write(file_data)
        return  path

    def mark_label(self,emailId,addLabels='Label_5163515677038728525',removeLabels=None):
        post_data={ "addLabelIds": [ addLabels ] }
        if removeLabels:
            post_data["removeLabelIds"] = [removeLabels]
        email = self.service.users().messages().modify(userId='me',id=emailId,body=post_data).execute()
        return email

    def get_labels(self):
        # Call the Gmail API
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        labels = list(filter(lambda x: x['type'] == 'user',labels))
        if not labels:
            label_request = { 'name':'processed','labelListVisibility':'labelShow','messageListVisibility':'show'}
            print('No user labels found. Creating %s' % label_request)
            resp = self.service.users().labels().create(userId='me',body=label_request).execute()
            labels = [resp]
        
        return labels
    
    def get_processed_label_id(self):
        labels = self.get_labels()
        label = filter(lambda l : 'processed' in l['name'], labels)
        if label: return list(label).pop().get('id')
        return labels.pop().get('id')

def main():
    gmail = GmailApp()

if __name__ == '__main__':
    main()
