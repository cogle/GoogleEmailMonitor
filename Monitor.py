#!./bin/python3.4
from __future__ import print_function

import os
import time
import httplib2

from apiclient import errors
from apiclient import discovery

import oauth2client
from oauth2client import tools
from oauth2client import client

from collections import deque

class EmailMonitor:

    #As long as the shut down signal isn't sent then run program
    run = True

    #GMail service
    service = None
    last_email_id = -1

    #Handle the email commands as they come.
    queue = deque([])

    def get_credentials(self):
        """
        Gets credentials so that one may access a particular google account
        """
        credential_dir = os.environ['GOOGLE_CREDENTIALS_DIR']
        credential_path = os.path.join(credential_dir,
                                       os.environ['GOOGLE_CREDENTIALS_FILE'])
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            print("Invalid credentials provided")
            os.exit(1)
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
        from_query = "from:" + str(os.environ['MY_PHONE_NUMBER'])


        """
        Set our final query as concatination of previous queries
        """
        query = from_query

        while self.run:
            try:
                response = self.service.users().messages().list(
                                                            userId='me',
                                                            q=query).execute()
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

                                self.queue.append(message_text['snippet'])

                        self.last_email_id = messages[0]['id']
                        self.handle_queue()




            except errors.HttpError:
                print('An error occurred: %s' % error)
                error_count = error_count + 1
                if error_count == 40:
                    print("Terminating program due to excessive errors")
                    exit(1)


            cur_count = cur_count + 1
            time.sleep(2)

    def handle_queue(self):
        while self.queue:
            command = str(self.queue.popleft()).lower().strip()
            if command == "end":
                self.run = False
                return

    def send_text_message(self, message):
        print(message)

    def run(self):
        self.get_credentials()
        self.get_service()

        #Check if the service was correctly set up
        if not self.service:
            print("Unable to correctly start service")
            os.exit(1)
        self.check_mail()




def main():
    """
    Script to monitor the status of an email account.
    """
    try:
        monitor = EmailMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("User terminated program")

if __name__ == '__main__':
    main()
