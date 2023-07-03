// rs.initiate({
//   _id: "replset",
//   members: [{
//     _id: 0,
//     host: "mongodb-primary:27017",
//     priority: 100
//   }, {
//     _id: 1,
//     host: "mongodb-secondary:27017",
//     priority: 10
//   }, {
//     _id: 2,
//     host: "mongodb-arbiter:27017",
//     arbiterOnly: true
//   }]
// });
// rs.initiate( {
//   _id : "my-replica-set",
//   members: [
//     { _id: 0, host: "localhost:27017" }
//   ]
// })

db.createUser({ user: "root", pwd: "password", roles: [] })
