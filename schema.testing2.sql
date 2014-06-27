-- Example table schema
-- To import your schemas into your database, run:
-- `mysql -u username -p database < schema.sql`
-- where username is your MySQL username
 
-- Load data into table
-- LOAD DATA LOCAL INFILE 'country.csv' INTO TABLE world_index
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY ''
-- LINES TERMINATED BY '\n'
-- IGNORE 1 LINES
-- (country, median_age, gdp, edu_index);

CREATE TABLE IF NOT EXISTS testing2 (
  id INT NOT NULL AUTO_INCREMENT,
  meanWordLength DECIMAL(3,1) NULL,
  meanSentLength DECIMAL(4,1) NULL,
  nChars INT NULL,
  nImages INT NULL,
  nLinks INT NULL,
  nSections INT NULL,
  nSents INT NULL,
  nRefs INT NULL,
  nWordsSummary INT NULL,
  pageId INT NULL,
  revisionId INT NULL,
  title VARCHAR(100),
  url VARCHAR(150),
  reading_ease DECIMAL(7,3) NULL,
  grade_level DECIMAL(5,3) NULL,
  ColemanLiauIndex DECIMAL(5,3) NULL,
  GunningFogIndex DECIMAL(7,3) NULL,
  ARI DECIMAL(7,3) NULL, 
  SMOGIndex DECIMAL(5,3) NULL,
  flags INT NULL,
  flagged INT NULL,
  featured INT NULL,
  score DECIMAL(4,2) NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;
