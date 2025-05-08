db = connect("mongodb://mongo:27017/Factee");

if (!db.getCollectionNames().includes("labels")) {
  db.createCollection("labels");
  db.users.insertMany([{
  "_id": {
    "$oid": "67cb143dea831f03968282f8"
  },
  "name": "upvote",
  "icon": "<i class=\"fa-solid fa-arrow-up\" style=\"color: #FFA500;\"></i>",
  "order": 0,
  "color": "#FFA500"
},{
  "_id": {
    "$oid": "67cb1456ea831f03968282f9"
  },
  "name": "downvote",
  "icon": "<i class=\"fa-solid fa-arrow-down\" style=\"color: #4052D6;\"></i>",
  "order": 1,
  "color": "#4052D6"
},{
  "_id": {
    "$oid": "67cb1463ea831f03968282fa"
  },
  "name": "fake",
  "icon": "<i class=\"fa-solid fa-xmark\" style=\"color: #FA5053\"></i>",
  "order": 3,
  "color": "#FA5053"
},{
  "_id": {
    "$oid": "67cb146bea831f03968282fb"
  },
  "name": "true",
  "icon": "<i class=\"fa-solid fa-check\" style=\"color: #50C878\"></i>",
  "order": 2,
  "color": "#50C878"
},{
  "_id": {
    "$oid": "67cb1473ea831f03968282fc"
  },
  "name": "paid",
  "order": 5,
  "icon": "<i class=\"fa-solid fa-dollar-sign\" style=\"color: #873260\"></i>",
  "color": "#873260"
},{
  "_id": {
    "$oid": "67cb147aea831f03968282fd"
  },
  "name": "free",
  "order": 4,
  "icon": "<i class=\"fa-solid fa-unlock\" style=\"color: #E4D96F\"></i>",
  "color": "#E4D96F"
}]);
}

if (!db.getCollectionNames().includes("types")) {
  db.createCollection("types");
  db.users.insertMany([{
  "_id": {
    "$oid": "67cb1d3eea831f0396828306"
  },
  "name": "Science",
  "color": "#007FFF"
},{
  "_id": {
    "$oid": "67cdbc8ab1e8a4614eb77882"
  },
  "name": "Mystic",
  "color": "#8000FF"
},{
  "_id": {
    "$oid": "67d2020fa88fa638fe2523bd"
  },
  "name": "Religion",
  "color": "#f7dc6f"
},{
  "_id": {
    "$oid": "67d202b8a88fa638fe2523be"
  },
  "name": "Domestic",
  "color": "#82e0aa"
}]);
}

if (!db.getCollectionNames().includes("facts")) {
  db.createCollection("facts");
}

if (!db.getCollectionNames().includes("sources")) {
  db.createCollection("sources");
}
