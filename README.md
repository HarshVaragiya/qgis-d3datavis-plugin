# QGIS D3 Date and Time Heatmap
This plugin is used to create D3 circular histogram heatmaps based on date and time fields in the data. Here is the plugin interface followed by an example use case of crime in Chicago.

![Circular Heatmap](tutorial/d3datavis.jpg)

## Examples
These examples make use of the [2006 Chicago crime data](https://data.cityofchicago.org/Public-Safety/Crimes-2001-to-present/ijzp-q8t2). In 2006 there were 367,968 crime incidents. That is a lot of crime for one year in just one city. Although this author is not trained in crime, some basic conclusions can be obtained by looking at the crime incidents based on the Month of the Year, Time of the Day, and Day of the Week. Here are the examples.

### Month of the year vs day of the week.

![Month vs day of the week](tutorial/month-dow.png)

By looking at this graph one can make some observations. The least amount of crime occurs during the months of January, February and March. This is probably due to the cold. If that is the case way does December have a high crime rate. That is probably because of the holiday season. 

### Hour of the day vs day of the week.

![Hour of the day vs day of the week](tutorial/hour-dow.png)

In this graph it appears that crime increase from 6pm to 11pm. The worst crime occurs from midnight to 1am. More difficult jobs must be taking place on the weekend where there is an increase of activity from 1am to 3am. During the day from Noon to 1pm there is also an increase of crime.

### Hour of the day vs month of the year

![Hour of the day vs month of the year](tutorial/hour-dow.png)

Here we see a similar pattern. Crime is less during January, February, and March. Crime increases starting from about 6pm to 11pm and then from Midnight to 1am plans are executed. This graph also shows the increased crime from Noon to 1pm.