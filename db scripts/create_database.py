import sqlite3

conn = sqlite3.connect(r'./Airport.db')
conn.execute("PRAGMA foreign_keys = 1")
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS Airplane (
               plane_id         VARCHAR (10) PRIMARY KEY
                                             UNIQUE
                                             NOT NULL,
               name             VARCHAR (20) NOT NULL,
               model            VARCHAR (20) NOT NULL,
               building_company VARCHAR (20) NOT NULL,
               been_in_use_from DATE         NOT NULL,
               fake_record      BOOLEAN      NOT NULL
            );
""")
conn.commit()
cur.execute("""CREATE TABLE IF NOT EXISTS Airline (
               airline_id      VARCHAR (10) PRIMARY KEY
                                             NOT NULL
                                             UNIQUE,
               name            VARCHAR (20) NOT NULL,
               registered_date DATE         NOT NULL,
               fake_record     BOOLEAN      NOT NULL
            );
""")
conn.commit()
cur.execute("""CREATE TABLE IF NOT EXISTS Flight (
               flight_id   VARCHAR (10) PRIMARY KEY
                                       UNIQUE
                                       NOT NULL,
               origin      VARCHAR (10) NOT NULL,
               destination VARCHAR (10) NOT NULL,
               date        DATE         NOT NULL,
               delay       TIME (7)     NOT NULL,
               plane_id    VARCHAR (10) NOT NULL,
               airline_id  VARCHAR (10) NOT NULL,
               fake_record BOOLEAN (10) NOT NULL,
               FOREIGN KEY (
                  plane_id
               )
               REFERENCES Airplane (plane_id),
               FOREIGN KEY (
                  airline_id
               )
               REFERENCES Airline (airline_id) 
);
""")
conn.commit()
cur.execute("""CREATE TABLE IF NOT EXISTS Passenger (
               passenger_id           VARCHAR (20) PRIMARY KEY
                                                   UNIQUE
                                                   NOT NULL,
               flight_id              VARCHAR (10) NOT NULL,
               SSN                    VARCHAR (20) NOT NULL,
               country_of_citizenship VARCHAR (20) NOT NULL,
               fake_record            BOOLEAN      NOT NULL,
               age                    INT          NOT NULL,
               created_at             DATE         NOT NULL,
               fullname               VARCHAR (30) NOT NULL,
               FOREIGN KEY (
                  flight_id
               )
               REFERENCES Flight (flight_id) 
);
""")
conn.commit()
cur.execute("""CREATE TABLE IF NOT EXISTS Tour (
               tour_id                VARCHAR (10) PRIMARY KEY
                                                   NOT NULL
                                                   UNIQUE,
               tour_manager_full_name VARCHAR (30) NOT NULL,
               company                VARCHAR (20) NOT NULL,
               origin                 VARCHAR (20) NOT NULL,
               destination            VARCHAR (20) NOT NULL,
               number_of_booking      INT          NOT NULL,
               departure_flight_id    VARCHAR (10) NOT NULL,
               arrival_flight_id      VARCHAR (10) NOT NULL,
               fake_record            BOOLEAN      NOT NULL,
               FOREIGN KEY (
                  departure_flight_id
               )
               REFERENCES Flight (flight_id),
               FOREIGN KEY (
                  arrival_flight_id
               )
               REFERENCES Flight (flight_id) 
);
""")
conn.commit()