CREATE TABLE categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  client_id INTEGER NOT NULL,
  name varchar(255)
);

CREATE TABLE "clients" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "name" varchar(255)
, notes text, hourly_rate integer default 100);

CREATE TABLE invoices(
  id integer primary key,
  client_id integer references clients(id),
  month date,
  status varchar(6) default 'billed',
  receipt blob,
  receipt_name varchar(255)
);


CREATE TABLE "time_entries" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "client_id" integer,
  "invoice_id" integer,
  "description" text, 
  "start_time" timestamp,
  "end_time" timestamp
, category_id integer, external_reference varchar(255));
