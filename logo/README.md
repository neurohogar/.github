# Logo

Three stacked river stones, rendered with Blender (Cycles) from `stones.py`: organic stone shapes, procedural granite material, studio lights and a green sweep backdrop.

```sh
blender -b -P logo/stones.py -- /path/to/out.png 1024   # output path, samples
```

Tested with Blender 5.2. The script uses the GPU (OptiX or CUDA) when available. The result is used as the organization avatar (1024×1024) and as the base of the profile banner.

## Banner

`profile/banner.jpg` is the same scene, wide, with the stones to the right and the tagline on the left:

```sh
blender -b -P logo/stones.py -- banner-raw.png 768 2560 800 -0.6 72   # output, samples, width, height, shift_x, lens
```

Then `logo/banner.html` lays the tagline over `banner-raw.png` (Atkinson Hyperlegible, the app's font) and a 2560×800 browser screenshot of it, saved as JPEG, is the banner.
