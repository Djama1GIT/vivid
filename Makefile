.PHONY: install frontend-install backend-install frontend-run backend-run fr br

install: frontend-install backend-install

frontend-install:
	cd client && npm install

backend-install:
	cd server && pip install -r requirements.txt

frontend-run:
	cd client && npm run build && npm start

backend-run:
	python server/main.py

fr: frontend-run

br: backend-run

