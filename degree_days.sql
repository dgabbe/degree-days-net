CREATE TABLE t_degree_days(
       id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
       weather_station_id TEXT,
       observed_at TEXT,
       degree_days REAL
);
