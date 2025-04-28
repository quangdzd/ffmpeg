effect = {
    "zoomin": "scale=10000:-1,zoompan=z='min(max(zoom,pzoom)+0.0015,1.5)':d=2400:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",

    "zoomout": "scale=10000:-1,zoompan=z='min(max(zoom,pzoom)-0.0015,5.5)':d=2400:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",

    "sliceleft": "zoompan=z=zoom:d=2400:x=50:y='ih/2-(ih/zoom/2)'",

    "sliceright": "zoompan=z=zoom:d=2400:x=50:y='ih/2-(ih/zoom/2)'"
}

transition = [
    "fade",
    "wipeleft",
    "wiperight",
    "slideright",
    "slideleft",
    "distance",
    "smoothleft",
    "smoothright",
    "circleopen",
    "circleclose",
    "vertopen",
    "vertclose",
    "diagtl",
    "diagtr",
    "diagbl",
    "diagbr"
]