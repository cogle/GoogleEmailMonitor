#!./bin/python3.4
from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools


class EmailMonitor:
    service = None

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
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    def run(self):
        self.get_credentials()
        self.get_service()
        if not self.service:
            print("Unable to correctly start service")
            os.exit(1)


def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    monitor = EmailMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
