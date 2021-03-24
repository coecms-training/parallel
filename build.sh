jupyter-book build .

URL=$PWD/_build/html/index.html

if [ -n "${WSLENV:-}" ]; then
    # Windows subsystem for linux
    URL='\\wsl$\Debian'$(tr '/' '\\' <<< $URL)
    /mnt/c/Windows/system32/cmd.exe /c start "$URL"
elif which xdg-open > /dev/null; then
    # Linux
    xdg-open "$URL"
elif which open > /dev/null; then
    # OSX
    open "$URL"
elif which explorer > /dev/null; then
    # Windows
    explorer "$URL"
else
    echo
    echo "----"
    echo "Can't find a way to open the URL automatically, please copy the URL above into your browser"
fi

