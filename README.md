

## Setup

1. If you don’t have Python installed, [install it from here](https://www.python.org/downloads/)

2. Clone this repository

3. Navigate into the project directory

   ```bash
   $ cd fake_commish
   ```

4. Create a new virtual environment

   ```bash
   $ python -m venv fc_venv
   $ . fc_venv/bin/activate
   ```

5. Install the requirements

   ```bash
   $ pip install -r requirements.txt
   ```

6. Make a copy of the example environment variables file

   ```bash
   $ cp .env.example .env
   ```

7. Add your [API key](https://beta.openai.com/account/api-keys) to the newly created `.env` file

8. Add your espn league id and the espn_s2 and swid cookies to the newly created `.env` file

9. Run Fake Commish. Specify the week number and the year for the wrapup (example below is for week 1 of 2022 season).

   ```bash
   $ python fake_commish.py 1 2022
   ```

