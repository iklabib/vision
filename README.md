# Vision
This repository contains integration to Hikvision and Dahua camera alarm. If you need to add another features please consult to provided PDF files. Good luck.

# Databases
```sql
-- Server = 10.19.101.42
-- Port = 5000
-- Database = DB_CCTV_SYS

CREATE TABLE "public"."event_notifications"(
   "id" text NOT NULL,
   "version" character varying(10),
   "ip_address" character varying(50),
   "ipv6_address" character varying(50),
   "port_no" integer,
   "protocol" character varying(10),
   "mac_address" character varying(20),
   "channel_id" integer,
   "date_time" timestamp with time zone,
   "active_post_count" integer,
   "event_type" character varying(50),
   "event_state" character varying(50),
   "event_description" text,
   "channel_name" character varying(100),
   CONSTRAINT "event_notifications_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "dahua_cam"."new_file_event"(
   "id" character(10) NOT NULL,
   "action" character varying(50) NOT NULL,
   "event_index" integer NOT NULL,
   "data_ids" int4[] NOT NULL,
   "data_region_names" text[] NOT NULL,
   "event_type" character varying(50) NOT NULL,
   "file_path" text NOT NULL,
   "file_index" integer NOT NULL,
   "file_size" integer NOT NULL,
   "storage_point" character varying(50),
   "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
   CONSTRAINT "new_file_event_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "dahua_cam"."video_motion"(
   "id" character(10) NOT NULL,
   "action" character varying(50) NOT NULL,
   "event_index" integer NOT NULL,
   "ids" int4[] NOT NULL,
   "region_names" text[] NOT NULL,
   "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
   CONSTRAINT "video_motion_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "dahua_cam"."video_motion_info"(
   "id" character(10) NOT NULL,
   "action" character varying(50) NOT NULL,
   "event_index" integer NOT NULL,
   "created_at" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
   CONSTRAINT "video_motion_info_pkey" PRIMARY KEY ("id")
);
```

