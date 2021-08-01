create database chatdb;
use chatdb;

create table user (
   userseq not null auto_increment primary key,
   userid varchar(50), 
   userpw varchar(50),
   userProfileImagePath varchar(255)
);

create table chatroom (
   roomseq not null auto_increment primary key,
   chatfrom varchar(50),
   chatto varchar(50),
   lastmsg varchar(1000),
   lastdate datetime
);


create table chat (
   chatseq not null auto_increment primary key,
   roomseq int,
   chatfrom varchar(50),
   chatto varchar(50),
   chatmsg varchar(1000),
   chatdate datetime
);
