# Keras
Keras is a web application for tracking billable work with Google Calendar integration. Time can be entered via the application or via Google Calendar. Keras supports multiple clients with different hourly rates. Time can be invoiced on a monthly basis and is exportable as a CSV (comma separated values) file. 

## Google Calendar.
Client time can be entered in Google Calendar and synced into Keras.

Let's say you built a new feature for client Foo on January 11, 2013 from 9:30 AM to 11:30 AM. You're event in Google Calendar would look like:


![solarized palette](https://github.com/jzellman/keras/raw/master/gcal.png)

Google Calendar event fields are mapped via:


    Google Event "What" - maps to Keras' time entry title and category fields (more below).
    Google Event "When" / Start and Stop  - maps to Keras' start and end time fields.
    Google Event "Description" - maps to Keras' description field.


## Getting Started

Configuration is done via config.py. There is a sample file which can be used as a starting point. You will need to add a username and password for basic authorization and your google username/password for syncing with your Google Calendar.

    cp config.py.example to config.py
    # edit config.py
    # create the db.
    sqlite3 billing.db < schema.sql
    # add required libs
    pip install -r requirements.txt
    # run the application    
    python app.py

# Getting Started with Development

Follow the above steps in "Getting Started" then install development dependencies:
    
    pip install -r dev_requirements.txt
    
After adding your feature run the tests, pep8, and pyflakes:

    python tests.py
    pep8 *.py
    pyflakes *.py

