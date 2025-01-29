CREATE DATABASE budgetapp;
USE budgetapp;

DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS recurringpayments;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  userid int NOT NULL AUTO_INCREMENT,
  username varchar(64) NOT NULL,
  pwdhash varchar(256) NOT NULL,
  PRIMARY KEY (userid),
  UNIQUE (username)
);
ALTER TABLE users AUTO_INCREMENT = 80001;

CREATE TABLE categories (
  categoryid int NOT NULL AUTO_INCREMENT,
  category varchar(256) NOT NULL,
  userid int NOT NULL,
  totalbudget float DEFAULT NULL,
  spent float NOT NULL,
  PRIMARY KEY (categoryid),
  FOREIGN KEY (userid) REFERENCES users (userid)
);
ALTER TABLE categories AUTO_INCREMENT = 1;

CREATE TABLE transactions (
  transactionid int NOT NULL AUTO_INCREMENT,
  userid int NOT NULL,
  name varchar(256) NOT NULL,
  cost float NOT NULL,
  category varchar(256) NOT NULL,
  transactiondate date NOT NULL,
  PRIMARY KEY (transactionid),
  FOREIGN KEY (userid) REFERENCES users (userid)
);
ALTER TABLE transactions AUTO_INCREMENT = 1;

CREATE TABLE recurringpayments (
  paymentid int NOT NULL AUTO_INCREMENT,
  paymentname varchar(256) NOT NULL,
  userid int NOT NULL,
  category varchar(256) NOT NULL,
  cost float NOT NULL,
  duedate date NOT NULL,
  PRIMARY KEY (paymentid),
  FOREIGN KEY (userid) REFERENCES users (userid)
);
ALTER TABLE recurringpayments AUTO_INCREMENT = 1;

DROP USER IF EXISTS 'budgetapp-read-only';
DROP USER IF EXISTS 'budgetapp-read-write';

CREATE USER 'budgetapp-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'budgetapp-read-write' IDENTIFIED BY 'def456!!';

GRANT SELECT, SHOW VIEW ON budgetapp.* 
      TO 'budgetapp-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON budgetapp.* 
      TO 'budgetapp-read-write';

FLUSH PRIVILEGES;