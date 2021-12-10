 <p align="center">
  <img width="200" src="https://cdn.dribbble.com/users/1501052/screenshots/5468049/searching_tickets.gif" alt="SearchX">
</p> 


<p align="center">
  
## This Is A Telegram Bot Written In Python For Searching Files In Our Beloved Google Drive.It Can Search In Multiple Shared Drive/Team Drives.
</p>

##Fork of iamLiquidX SearchX Bot with many new features

##Features added by me
- Ability to choose b/w Recursive Search and normal Search
- Ability to choose b/w Files and folder or both while searching
- Define Authorized Chat in Config.env
- Define token.pickle url in config.env
- Auto generating Telegraph Token, no need to generate manually

Here Are Some Things To Get You Started.👇

### 👉[How To Deploy]()
- Fork this repo
- Fill configs in config.env
- Fill drive_folder accordingly or you can run driveid.py
- drive_folder format - Drive Name, Drive ID, Index Url Here, Give Space Between Them.
- Go to Heroku 
- Create new app
- Go to App's Deploy Tab
- Choose Github connect and connect your github account with Heroku
- Search for this repo
- select it and deploy
Will add guide and github actions support soon 
untill you can use your mind and deploy on heroku using

### 👉Deploy using Github actions
- Fork this repo
- Go to Repo setting
- Go to Secrets
- File the value of given Secrets
 ```
 - HEROKU_API_KEY - Account API
 - HEROKU_EMAIL - Heroku Email
 - HEROKU_APP_NAME - Heroku App name
 - CONFIG_FILE_URL - Your Config file url, you can upload your config file url to a private repo and use its RAW link.
 ```
- After filling these Secrets go to Action tab of repo
- Select Workflow name "Manually Deploy to Heroku" and clik on "Run Workflow"
- You check actions log and heroku log if you face any error

## Drive_Folder guide
```
- Drive_folder format
- Drive Name, Drive ID, Index Url Here, Give Space Between Them.
- Ex. Main-Drive 0ABoKpdhdjItUk9PVA https://dl.testing.workers.dev/0:
Second-Drive 0ABoigoqjshsk9PVA https://dl.noformat.workers.dev/0:
- Seprate each drive with line
```

## MULTI_SEARCH_URL Guide
```
MULTI_SEARCH_URL
**Example:**<br>
`Before: https://gist.githubusercontent.com/arshsisodiya/8cce4a4b4e7f4ea47e948b2d058e52ac/raw/19ba5ab5eb43016422193319f28bc3c7dfb60f25/gist.txt` <br>
`After:  https://gist.githubusercontent.com/arshsisodiya/8cce4a4b4e7f4ea47e948b2d058e52ac/raw/gist.txt`
```

# Credits 👇
1.[Sreeraj V R](https://github.com/SVR666)- Created Search Bot.
2.[AnimeKaizoku](https://github.com/AnimeKaizoku)- Fixes & Improvement.
3.[Sunil Kumar](https://github.com/iamLiquidX)-  SearchX