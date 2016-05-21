#!./bin/python3.4
from __future__ import print_function

import os
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
    last_email_id = None

    #Handle the email commands as they come.
    queue = deque([])

    def get_credentials(self):
        """
        Gets credentials so that one may access a particular google account
        """
        credential_dir =   os.environ['GOOGLE_CREDENTIALS_DIR']
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
        response = self.service.users().messages().list(userId='me',
                                                        q='').execute()
        print(response)

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
    monitor = EmailMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
