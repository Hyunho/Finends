# Finends Strategy Viewer

`chilmyeonjo/web` is a read-only Rails app that scans `chilmyeonjo/strategies` and renders strategy documents in the browser.

## Scope

- Strategy index page
- Strategy detail page with grouped documents and history
- Markdown viewer for strategy docs and archived retrospectives
- Source and test file listing for orientation

The app does not execute Python strategy code. It only reads repository files.

## Run

```bash
source ~/.zshrc
cd chilmyeonjo/web
bundle install
bin/rails server
```

Open `http://127.0.0.1:3000`.

## Test

```bash
source ~/.zshrc
cd chilmyeonjo/web
bin/rails test
```
