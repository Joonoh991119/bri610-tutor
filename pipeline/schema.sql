--
-- PostgreSQL database dump
--

\restrict qKraAwrxECQMaq2HxRkhBBK8i8cgHua7b8pyhIitm2WdfD96mxbieKkEVfOp8Zk

-- Dumped from database version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: qc_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qc_log (
    id integer NOT NULL,
    source_table character varying(30) NOT NULL,
    source_id integer NOT NULL,
    check_name character varying(50) NOT NULL,
    passed boolean NOT NULL,
    details jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: qc_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.qc_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: qc_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.qc_log_id_seq OWNED BY public.qc_log.id;


--
-- Name: slides; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.slides (
    id integer NOT NULL,
    lecture character varying(10) NOT NULL,
    lecture_title text,
    page_num integer NOT NULL,
    content text,
    topics text DEFAULT ''::text,
    img_path text,
    embedding public.vector(2048),
    qc_status character varying(20) DEFAULT 'pending'::character varying,
    qc_notes text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: slides_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.slides_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: slides_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.slides_id_seq OWNED BY public.slides.id;


--
-- Name: textbook_pages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.textbook_pages (
    id integer NOT NULL,
    book character varying(50) NOT NULL,
    page_num integer NOT NULL,
    chapter character varying(10),
    chapter_title text,
    section_title text,
    content text,
    content_length integer,
    has_figures boolean DEFAULT false,
    has_equations boolean DEFAULT false,
    has_references boolean DEFAULT false,
    has_captions boolean DEFAULT false,
    n_drawings integer DEFAULT 0,
    n_raster_images integer DEFAULT 0,
    page_type character varying(20),
    img_path text,
    text_embedding public.vector(2048),
    image_embedding public.vector(2048),
    qc_status character varying(20) DEFAULT 'pending'::character varying,
    qc_notes text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: textbook_pages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.textbook_pages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: textbook_pages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.textbook_pages_id_seq OWNED BY public.textbook_pages.id;


--
-- Name: qc_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qc_log ALTER COLUMN id SET DEFAULT nextval('public.qc_log_id_seq'::regclass);


--
-- Name: slides id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slides ALTER COLUMN id SET DEFAULT nextval('public.slides_id_seq'::regclass);


--
-- Name: textbook_pages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.textbook_pages ALTER COLUMN id SET DEFAULT nextval('public.textbook_pages_id_seq'::regclass);


--
-- Name: qc_log qc_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qc_log
    ADD CONSTRAINT qc_log_pkey PRIMARY KEY (id);


--
-- Name: slides slides_lecture_page_num_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slides
    ADD CONSTRAINT slides_lecture_page_num_key UNIQUE (lecture, page_num);


--
-- Name: slides slides_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slides
    ADD CONSTRAINT slides_pkey PRIMARY KEY (id);


--
-- Name: textbook_pages textbook_pages_book_page_num_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.textbook_pages
    ADD CONSTRAINT textbook_pages_book_page_num_key UNIQUE (book, page_num);


--
-- Name: textbook_pages textbook_pages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.textbook_pages
    ADD CONSTRAINT textbook_pages_pkey PRIMARY KEY (id);


--
-- Name: idx_slides_fts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_slides_fts ON public.slides USING gin (to_tsvector('english'::regconfig, ((COALESCE(content, ''::text) || ' '::text) || COALESCE(topics, ''::text))));


--
-- Name: idx_slides_qc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_slides_qc ON public.slides USING btree (qc_status);


--
-- Name: idx_tp_fts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tp_fts ON public.textbook_pages USING gin (to_tsvector('english'::regconfig, ((COALESCE(content, ''::text) || ' '::text) || COALESCE(section_title, ''::text))));


--
-- Name: idx_tp_qc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tp_qc ON public.textbook_pages USING btree (qc_status);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA public TO tutor;


--
-- PostgreSQL database dump complete
--

\unrestrict qKraAwrxECQMaq2HxRkhBBK8i8cgHua7b8pyhIitm2WdfD96mxbieKkEVfOp8Zk

