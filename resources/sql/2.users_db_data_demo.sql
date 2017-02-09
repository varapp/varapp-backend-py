CREATE DATABASE  IF NOT EXISTS `users_db` /*!40100 DEFAULT CHARACTER SET latin1 */;
USE `users_db`;

INSERT INTO `db_accesses` VALUES (NULL,NULL,NULL,NULL,1,1,1,1);
INSERT INTO `people` VALUES (NULL,NULL,NULL,NULL,1,1,'Admin','Allmighty','','','','',0,NULL);
INSERT INTO `roles` VALUES (NULL,NULL,NULL,NULL,1,1,'superuser',1,1,1),(NULL,NULL,NULL,NULL,1,2,'admin',2,1,0),(NULL,NULL,NULL,NULL,1,3,'head',3,1,0),(NULL,NULL,NULL,NULL,1,4,'guest',4,0,0),(NULL,NULL,NULL,NULL,1,5,'demo',5,0,0);
INSERT INTO `users` VALUES (NULL,NULL,NULL,NULL,1,1,'admin','abOV.DfJmdnYw','abcdefghijklmnopqrs','demo@demo.com','admin',NULL,NULL,1,1);
INSERT INTO `variants_db` VALUES (NULL,NULL,NULL,NULL,1,1,'demo_mini','demo_mini','demo_mini.db','resources/db/','e25b76e60082485158292750c239a2d255b742eb','My first Gemini db',NULL,NULL);

