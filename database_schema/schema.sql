CREATE TABLE public.categories
(
    id uuid NOT NULL,
    name character varying NOT NULL UNIQUE,
    PRIMARY KEY (id)
);

CREATE TABLE public.spendings
(
	id uuid NOT NULL,
	amount numeric NOT NULL,
	item character varying NOT NULL,
	date date NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE public.spendings_categories
(
	spending uuid,
	category uuid,
	PRIMARY KEY(spending, category),
	FOREIGN KEY(spending) REFERENCES public.spendings(id) ON DELETE CASCADE,
	FOREIGN KEY(category) REFERENCES public.categories(id) ON DELETE CASCADE
);