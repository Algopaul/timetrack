install: ${HOME}/.cache ${HOME}/.local/bin
	sqlite3 ${HOME}/.cache/pstimetrack.db < setup.sql
	chmod +x main.py
	cp main.py ${HOME}/.local/bin/tt
	cp tracker_completions.sh ${HOME}/.cache/pstimetrack_completions.sh
	echo "Add \"source ${HOME}/.cache/pstimetrack_completions.sh\" to your zshrc"

