ffmpeg -framerate 30 -start_number 750 -i ./data/maps/map_%d.png -pix_fmt yuv420p -vf scale=800:600 -c:v libx264 ./data/map_animation.mp4
ffmpeg -i ./data/map_animation.mp4 map_animation.gif
