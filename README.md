# football-automation-and-dashboarding-project

## Overview

This repo is the basis of a portfolio project I created in my career break prior to going travelling in Australia and New Zealand.

After watching the 2026 World Cup in North America, I began thinking about how tactics and stats may have changed over the years due to playstyle changes and squads adding new players. I was particularly interested in how passes and build up play has changed, since we have been transitioning into a playstyle that relys heavily on ball playing centre backs to hold the ball, and play transitional passes to start attacking phases.

For non football fans, this may sound like a foreign language, but the basic idea is this:

- In the past, the midfielders would have the most passes, meaning they would be the players to move the ball up the pitch more often than any other roles.
- Nowadays, this is still something that midfields do, but more modern managers have been asking their defenders to pick up this role more too.

After some research, I found that there is a Python package that has data included for some football recent competitions, such as the last couple of World Cups and Euros (it is yet to be updated with the 2026 World Cup). This includes data on the Matches played, the Events in each match (passes, shots, tackles, etc), and the lineups and substitutions made as well.

Going into this project, my main goals were:

1. Create a productionised workflow that will create a Data Warehouse storing the StatBombPY data.
2. Implement a medallion structure to the Data Warehouse, using Bronze for the raw data with some cleaning, Silver for the full cleaned version and gold for the production tables.
3. Create a Power BI report focusing around passes
4. Implement incremental loading and SCD tracking for the football data, ensuring the workflow is optimised.
5. Spend a minimal amount of money, but note down ideas on how to improve the process if money were to be spent

On the financial perspective, I have used SQLite, which stores the databases locally rather than using a PostgresSQL server, which is my preference.

## How to run yourself

As of August 2026, I have been unable to find a reliable way to publish the report to Power BI online without an organisation account, which means the dashboard cannot be viewed unless set up locally. Unfortunately, this means you are unable to view the dashboard personally without setting up all of the settings and databases locally.
To circumvent this, I have recorded a 20 minute demo to show you how I used this dashboard to understand how Croatia used their Midfield 3 of Modric, Kovacic and Brozovic to build up play compared to the way England built up play in the 2022 World Cup. This can be found as an unlisted YouTube video here: [Football Analysis Demo](https://youtu.be/EuJn90Glt7Q)

If you would like to try it out for yourself, please take a look at this file for more information on how to run it locally: [Running Locally](./data_extraction_workflow/docs/running-locally.md)

## Limitations

As mentioned above, Power BI is limited to only being available for organisations, so I am unable to publish and share the report manually. Moreover, the process to set up the dashboard locally is rather long winded, since SQLite databases are locally stored. This is a further limitation of the project.
Finally, StatsBombPY has a limited selection of competitions and matches, so the sample size is quite small.

## Changes/Upgrades I would make in the future

1. Upgrade from SQLite to PostgresSQL in Azure - This is a no-brainer for me. Having a cloud server would improve the process drastically, since connection to Power BI would be improved, and Postgres allows for multiple schemas in a server, whereas SQLite is limited; each database I've created would be a schema in a Postgres Server.
2. Power BI Reporting - As you'll see in the demo, we are limited to just a Homepage and Passing dashboards. If I spent more time on the project, I would expand on the categories to look at shots, defensive contributions and saves for goalkeepers. This would transition the report into more of a scouting report for a user to view players that performed well at tournaments.
3. Change of datasource - As mentioned in the limitations, the StatsBombPY data is limited, so if another API exists with more data available, that change would be a must to improve the sample size.
4. Azure Function Apps - If I were to input some money into this project, I would also look to create the refresh process using an Azure Function App, since this would ensure the refresh occurred regularly.
