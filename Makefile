.PHONY: install frontend-install backend-install frontend-run backend-run fr br

install: frontend-install backend-install

frontend-install:
	cd client && npm install

backend-install:
	cd server && python3 -m venv venv && source venv/bin/activate && python3 -m pip install -r requirements.txt

frontend-run:
	cd client && npm run build && npm start

backend-run:
	cd server && source venv/bin/activate && python3 main.py

fr: frontend-run

br: backend-run

