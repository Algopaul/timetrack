# _tracker

# Helper function to get the list of project names
_get_tracker_projects() {
  local projects
  projects=("${(@f)$(sqlite3 ${HOME}/.config/timetracking/tracker.db "SELECT name FROM projects;")}")
  _describe 'projects' projects
}

# Main completion function
_tracker() {
  local curcontext="$curcontext" state line
  typeset -A opt_args

  _arguments \
    '1:command:(create start stop status worked_today current)' \
    '2:project name:_get_tracker_projects'
}

compdef _tracker tt
