# Payslip Checking Assistance Tool

Aims to **minimise the time** it takes to check your payslip, so you can get back to living your life without the government rolling you for your net worth.

> [!CAUTION]
> PayCAT is not perfect and is NOT extensively bug-tested. It was created by one person, partly as a hobby-project. Please do not screenshot or directly reference the output of PayCAT in communications with your employer. PayCAT is quite obviously not financial advice. Opinions expressed are solely my own and do not express the views or opinions of my employer. 

## Installation

There are two download options:

1. Download a packaged up version of the code from the "Releases" section on the right.
	- No extra work required.

1. Clone this repository and run it yourself.
	- Requires Python 3.11.7 or greater and some amount of command-line experience.
	- Clone the repository with `git clone https://github.com/samRiley04/PayCAT`, or download it manually as a .zip file.
	- Then with [pip installed](https://pypi.org/project/pip/), do `pip install -r requirements.txt` to download the required python packages.
	- Finally, run PayCAT with `python3 app.py`

## Usage

See static/user-help/user-help.md for a comprehensive explanation of functionality. Excerpts below:

> ### Steps to Create a "Compare" Mode Study
> 1. Add a new study (Top bar -> "New")
> 1. In the compare mode (purple) column, click "choose file" and select your payslip.
> 1. Below that, click the other "choose file" and select your roster. Some extra options will appear because you have selected a roster file
> 1. Fill in the required details:
>	- Roster type simply represents the general structure of your roster - click the "?" icon for representative photos. 
>	- Your name - should be verbatim as it is written in the roster, including capital letters
>	- Dates - should be the same dates that your payslip applies to
> 5. Click "Create Compare".

> ### Steps to Create a "View" Mode Study
> 1. Add a new study (Top bar -> "New")
> 1. In the view mode (blue) column, click "choose file" and select your file.
> 1. If you selected a roster, fill out the extra boxes as you would when creating a Compare mode study.
> 1. Click "Create View"

## Included in PayCAT

Other source code included in this repository.

- (JS) jQuery - MIT license
- (JS) [md-block](https://github.com/leaverou/md-block) - MIT license
- Bootstrap v5.3.2 - MIT license