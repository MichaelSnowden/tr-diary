# Tom Riddle's Diary
![demo](demo.gif)

This is a gift I made for my friend as just a dumb way for us to talk to each other. I found it pretty technically 
interesting actually. 

## Features
- Drawing
- Typing
    - No punctuation
    - No backspace
    - It will wrap to next line automatically, but words will be split
- Unlimited connections to a given page (given that the server doesn't crash)
- Private pages (just change the last path of the url e.g. `/secret_page`)

## Implementation
- Server
    - Flask
    - Flask-Sockets
    - ~100 lines because all it does is forward messages to everyone on the same page
- Client
    - The hardest part here is figuring out the data model and the rendering
    - I 100% copied my idea for fading out the lines from [this guy](https://stackoverflow.com/a/24309167/2770572)
        - However, I'd really like to try something different because this approach erases at a very strange rate, essentially very quickly erasing a lot and then leaving permanent traces.
    - The DOM is pretty much just a square canvas that resizes with the window to fit along the smallest dimension
    - The data model is a nested structure that looks like this
        - Writer
            - A writer has many strokes
            - Stroke
                - A stroke has many points
                - Point
                    - X,Y coordinates in [0,1]
                    - A timestamp
    - The render loop looks like this
        - Remove "expired" points (ones that have been on the screen for more than 8 seconds)
        - Slowly fade in the background (this gradually erases any points that aren't immediately redrawn in the next step)
        - Redraw existing points
    - The font rendering was another tricky part
        - Instead of parsing font files or using an external library to do so, I came up with a very simple but hacky approach
        - I wrote what is essentially a script in "generate_font.html"
            - In this file, I console.log each letter and then draw it. When I left click, I end the "recording" and export the strokes to a dictionary mapping characters to their strokes
            - This file ended up being 268KiB, which is about 20x what the size of a font file should be.
                - I ended up not needing the timestamp data in the font files so I think I can compress this data to x,y coordinates (with some delimiters for the strokes)
                - The file can definitely be compressed to just each character's strokes which is roughly 2 points * 4 bytes per float * 26 characters * 73 points per character = ~15KiB
        - The webpage just replays those strokes for the character you type both into the `writers` data structure and across the websocket broadcast to everyone on the page

## Future ideas (highest to lowest priority)
- Don't send characters as individual points (this is insanely inefficient but was the easiest thing at the moment)
- Use WebRTC instead of connecting to a central server
    - Obviously the central server is still needed to, at the very least, act as the "signaling server" to officiate the discovery of peers
- Support punctuation
- Support backspacing
- Compress the font file (I think this can get down to 17% by using a binary file format)
    - Each character could also be loaded async but I don't think this is very useful
- Use binary websocket messages instead of JSON 