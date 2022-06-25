## General

### Coordinate System

Coordinate starts from the lower left of the plane as if we are looking at the first quadrant of a plane. This choice is made because of several problems seem to follow such conventions, such as this [sorting one](../ARCdata/data/training/08ed6ac7.json). 

```
(0, m-1) ------------- (n-1, m-1)
|                          |
|                          |
|                          |
|                          |
|                          |
(0, 0) --------------- (n-1, 0)
```

However, when we store the contents of a problem, it still goes from top to down, as the convention of programming languages and printing. 

## Interpreter 

Interpreter searches for objects in an image. In a search program term, state is a canvas and edge is an object. When we draw an object on canvas old to get canvas new, it is equivalent to drawing an edge from state old to state new. 

### Object Representation

An `object` object as in [obj_a_log.py](obj_a_log.py) contains the following attributes: `type, xs, ys, color, l, xlen, ylen`. A detailed documentation can be found in the linked python file. These attributes are enough to describe an edge when we want to reconstruct the path from start state to final state. 

In addition, when we hand annotate an ARC problem, we record 3 more attributes:
- `layer`: the depth of this object. Objects with a higher layer number are closer to the user, so objects with a higher layer occlude the ones with a lower layer number if they do overlap. 0 is background (We don't record background unless it has a different color than black, so it is a non-black rectangle with the same dimension of the canvas). When there is no occlusion, all objects have layer equal to 1. 
- `outbound`: true if a part of this object is out of this canvas, so it cannot be shown, but a human knows there is this unshown part. 
- `bitmap`: contents of this bitmap if this is a bitmap object. null if this object is not a bitmap. Recorded in the same way as a canvas. See [!!! NOT DONE !!!]() for an example. 

Hand annotated solutions are stored in the file with the following naming format: `s_<taskname>_<i/o>.json`. So if we are writing the solution to input of task 025d127b, we will store it in `s_025d127b_i.json`. 

## Generative ARC

### `template.py` Task Template

Every task should follow the instructions and naming conventions given in [`template.py`](template.py). More than a template, it should be viewed as an interface.

### `export_json.py`

This program is used to generate a certain number of input output pairs of a particular program, and output the generated canvas in json. The json format follows the format in the original jsons given. Use argument `TASK_NAME` and `GEN_NUM` to specify which task you want to generate samples for, and how many samples you want. 

### Calling Convention

- When specify a color, use `Color.<color_name>` as specified in [`color.py`](API/color.py). For example, if want to use cobalt blue, don't use `1`. Instead, use `Color.Cobalt`
- When to use `rand_division(1, n, l)` and when to use `rand_sample(n, l)`?
  These two functions both return `n` random elements from list `l`, but `rand_division` returns a sorted list, while `rand_sample` returns an unsorted one.
