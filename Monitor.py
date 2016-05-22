#!./bin/python3.4
from __future__ import print_function

import os
import sys
import time
import base64
import httplib2
import mimetypes

from MySocket import MySocket

from apiclient import errors
from apiclient import discovery

import oauth2client
from oauth2client import tools
from oauth2client import client

from collections import deque


from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

class EmailMonitor:

    #As long as the shut down signal isn't sent then run program
    run = True

    #GMail service
    service = None
    last_email_id = -1

    #Handle the email commands as they come.
    queue = deque([])

    #Class to send messages to our socket
    socket_class = MySocket()

    def get_credentials(self):
        """
        Gets credentials so that one may access a particular google account
        It is super important that you have full access to aforementioned account.
        """
        credential_dir = os.environ['GOOGLE_CREDENTIALS_DIR']
        credential_path = os.path.join(credential_dir,
                                       os.environ['GOOGLE_CREDENTIALS_FILE'])
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            print("Invalid credentials provided")
            socket_class.shutdown()
            sys.exit(1)
        return credentials

    def get_service(self):
        """
        Sets up the service for future usage.
        """
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    def check_mail(self):

        """
        The count serves to help us narrow down the time range, by counting
        iteration we can determine how much time has passed and therefore
        update our query accordingly
        """
        cur_count = 0


        error_count = 0

        """
        Search for messages from a given phone number
        """
        from_query = "from:" + str(os.environ['PHONE_NUMBER_EMAIL'])

        """
        Set our final query as concatination of previous queries
        """
        query = str(from_query + " "
                    + "in:inbox" +" "
                    + "is:unread")

        while self.run:
            try:
                response = (self.service
                            .users()
                            .messages()
                            .list(userId='me',
                                  q=query).execute())

                messages = []
                if 'messages' in response:
                    messages.extend(response['messages'])
                    """
                    First message will be different
                    """

                    if messages[0]['id'] != self.last_email_id:
                        for message in messages:
                            if message['id'] == self.last_email_id:
                                break
                            else:
                                message_text = (self.service.users()
                                                .messages()
                                                .get(userId='me',
                                                     id=message['id'],
                                                     format='raw').execute())
                                message_info = {'msg_id' : message['id'],
                                                'msg_txt' : message_text['snippet']}
                                self.queue.append(message_info)

                        self.last_email_id = messages[0]['id']
                        self.handle_queue()




            except errors.HttpError as error:
                print('An error occurred: %s' % error)
                error_count = error_count + 1
                if error_count == 40:
                    print("Terminating program due to excessive errors")
                    self.send_text_message("Terminating Program due to excessive errors")
                    socket_class.shutdown()
                    sys.exit(1)


            cur_count = cur_count + 1
            time.sleep(2)

    def handle_queue(self):
        while self.queue:
            info_dic = self.queue.popleft()

            message_id = info_dic['msg_id']
            command = str(info_dic['msg_txt']).lower().strip()

            if command == "complete shutdown":
                self.run = False
                self.mark_as_read(message_id)
                self.socket_class.send_message("end")
                self.send_text_message('Shutting Down after marking messages')
            #So here we would actually handle the commands
            elif self.run:
                self.socket_class.send_message(command)
                self.mark_as_read(message_id)
            #This exists in order to mark messages as read/
            else:
                print("Marking message: " + command)
                self.mark_as_read(message_id)

    def send_text_message(self, message_text):
        message = MIMEText(message_text)
        message['to'] = os.environ['PHONE_NUMBER_EMAIL']
        message['from'] = os.environ['GMAIL_PI_EMAIL']
        raw = base64.urlsafe_b64encode(message.as_bytes())
        raw = raw.decode()
        body = {'raw': raw}
        try:
            message = (self.service.users()
                       .messages().send(userId='me', body=body)
                       .execute())

        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def run(self):
        self.get_credentials()
        self.get_service()
        #Check if the service was correctly set up
        if not self.service:
            print("Unable to correctly start service")
            socket_class.shutdown()
            sys.exit(1)
        self.check_mail()

    def send_unknown_error_alert(self):
        self.send_text_message("Unknown error occured")

    def send_final_shutdown_text(self):
        self.send_text_message("Program has concluded successfully")

    def mark_as_read(self, msg_id):
        payload = {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}
        try:
            message = (self.service.users()
                       .messages().modify(userId='me', id=msg_id,
                                          body=payload).execute())
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

def main():
    """
    Script to monitor the status of an email account.
    """
    monitor = EmailMonitor()
    try:
        monitor.run()
        monitor.send_final_shutdown_text()
    except KeyboardInterrupt:
        print("User terminated program")
    except:
        print("Unknown error")
        monitor.send_unknown_error_alert()
        raise

if __name__ == '__main__':
    main()
