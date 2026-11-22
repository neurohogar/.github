# Logo

Three stacked river stones, rendered with Blender (Cycles) from `stones.py`: organic stone shapes, procedural granite material, studio lights and a green sweep backdrop.

```sh
blender -b -P logo/stones.py -- /path/to/out.png 1024   # output path, samples
```

Tested with Blender 5.2. The script uses the GPU (OptiX or CUDA) when available. The result is used as the organization avatar (1024×1024) and, scaled down, as `profile/logo.jpg`.
