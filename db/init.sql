create database chatdb;
use chatdb;

create user 'arangtest'@'%' identified by 'testpass';

create table user (
   userseq int not null auto_increment primary key,
   userid varchar(50), 
   userpw varchar(50),
   userProfileImagePath varchar(255)
);

create table chatroom (
   roomseq int not null auto_increment primary key,
   chatfrom varchar(50),
   chatto varchar(50),
   lastmsg varchar(1000),
   lastdate datetime
);

create table chat (
   chatseq int not null auto_increment primary key,
   roomseq int,
   chatfrom varchar(50),
   chatto varchar(50),
   chatmsg varchar(1000),
   chatdate datetime
);

create table flag (
   flag varchar(255)
);

insert into flag values("fiesta{this_is_test_flag}");

grant select, insert on chatdb.user to 'arangtest'@'%';
grant select, insert on chatdb.chatroom to 'arangtest'@'%';
grant select, insert on chatdb.chat to 'arangtest'@'%';
grant select on chatdb.flag to 'arangtest'@'%';
flush privileges;