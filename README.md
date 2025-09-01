# Datawarehouse

data-warehouse/
├── api/
│   ├── sensor.py                  
│   └── video.js               
│                 
├── app/
│   ├── auth.py                  
│   ├── database.py              
│   ├── models.py              
│   ├── schmas.py                  
│   └── routes/ admin.py
|        ├──admin.py
|        └── protected.py
|
├── ml_deshboard/
│   ├── backend/                 
│   |    ├── ml_routes.py              
│   |    └── server.py              
│   ├── frontend 
|   |    ├──app.js
|   |    └── index.html
|   |
│   └── assets/
|        └──styles.css      
| 
├── static/
│   ├── main.js                  
│   └── chart/             
│       ├── chartUtils.js              
│       ├── sensorBarChart.js                  
│       ├── sensorLineChart.js
|       └── sensorPieChart                       
│
├── storage/
│   ├── create_db.py              
│   ├── sensors/ 
|   |     └── sensor_data.csv 
|   ├── videos/
|   |   ├── NewVideo.mp4                 
│   |   ├── sample_video.mp4
|   |   └── Test.mp4            
│   └── sensor.db                  
│
├── .env                         
├── Specification.md             
├── README.md                    
└── run.sh / start.bat          
