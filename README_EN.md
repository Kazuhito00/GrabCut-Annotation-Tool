# GrabCut-Annotation-Tool
https://user-images.githubusercontent.com/37477845/131681382-020df52c-dbc7-4750-80d1-42ff141ba829.mp4

Annotation tool using GrabCut() of OpenCV.<br>
It can be used to create datasets for semantic segmentation.<br>
\* Due to GrabCut's algorithm, it is suitable for annotation of data with clear boundaries.<br>

# Requirement 
* opencv-python 4.5.2.54 or later
* Pillow 7.2.0 or later
* PySimpleGUI 4.32.1 or later

# Directory
<pre>
│  app.py
│  config.json
│  
├─core
│  │  gui.py
│  └─util.py
│          
├─input
│      
└─output
    ├─image
    └─annotation
</pre>

#### app.py, core/gui.py, core/util.py
Source code.

#### input
Image files are stored in this directory.

#### output
Directory to save annotation results.
* image：The resized image is stored here
* annotation：Annotation result is stored her<br> * Saved in PNG format in palette mode

# Usage
Start it with the following command.
```
python app.py
```
The following options can be specified.
* --input<br>
Input image storage path<br>
Default：input
* --output_image<br>
Storage path of annotation result (image)<br>
Default：output/image
* --output_annotation<br>
Storage path of annotation result (segmentation image)<br>
Default：output/annotation
* --config<br>
Configuration file to be loaded<br>
Default：config.json

# Using GrabCut-Annotation-Tool
### File select
You can switch the annotation target by clicking the file list.<br>
keyboard shortcut 　↑、p：preview file　↓、n：next file<br>
<img src="https://user-images.githubusercontent.com/37477845/131686101-c94132bc-4b76-488a-85fe-69d9d9c216bd.png" width="80%">

### Initial ROI designation
You can specify the initial ROI by right-drag the mouse when "Select ROI" is displayed.<br>
<img src="https://user-images.githubusercontent.com/37477845/131687291-4f4c06d5-89fa-452d-925f-5576edc5af64.png" width="80%"><br><br>

After the drag is finished, GrabCut processing is performed.<br>
<img src="https://user-images.githubusercontent.com/37477845/131687690-295dc463-f82e-447b-86f8-65bbf6cf4e2d.png" width="80%"><br><br>

The area is selected.<br>
<img src="https://user-images.githubusercontent.com/37477845/131688127-3fc1c00e-0f99-435a-aa29-d9392c7af6d0.png" width="80%"><br><br>

### Background designation
You can specify the background by dragging the right mouse button.<br>
<img src="https://user-images.githubusercontent.com/37477845/131688309-c47184d9-f793-49f0-aa26-445ea2c2b431.png" width="80%"><br><br>

<img src="https://user-images.githubusercontent.com/37477845/131688599-dc78e307-8a3b-4ec7-a9be-05325486ee5e.png" width="80%"><br><br>

### 前景指定
You can switch to foreground specification by unchecking "Manually label background".<br>
keyboard shortcut　Ctrl<br>
<img src="https://user-images.githubusercontent.com/37477845/131688947-ab0505ca-8413-4afe-8d5a-c42ae1f25a3f.png" width="80%"><br><br>

You can specify the foreground by dragging the right mouse button.<br>
<img src="https://user-images.githubusercontent.com/37477845/131689310-5447308d-2019-48d7-8a43-df7707969599.png" width="80%"><br><br>

<img src="https://user-images.githubusercontent.com/37477845/131689509-ea0597a4-939a-4821-a077-40720687e8b1.png" width="80%"><br><br>

### Class ID switching
You can switch the class ID by pressing the check box.<br>
The single digit ID can be switched with a shortcut key.<br>
keyboard shortcut　0-9<br>
<img src="https://user-images.githubusercontent.com/37477845/131690009-862e763d-9714-4420-bf9c-7185daa0bbff.png" width="80%"><br><br>

After switching the class ID, it is necessary to specify the ROI.<br>
<img src="https://user-images.githubusercontent.com/37477845/131690463-667530d6-6e89-4eec-88ff-8a5aaf55a8a1.png" width="80%"><br><br>

<img src="https://user-images.githubusercontent.com/37477845/131690674-293340bc-eedb-48dc-9a20-8a5e4e61d1db.png" width="80%"><br><br>

### Auto save
Resized images and annotation images are automatically saved for each GrabCut process.<br>
<img src="https://user-images.githubusercontent.com/37477845/131691035-ab98cf83-f659-4efe-89aa-896badcee985.png" width="50%"><br><br>

If you do not want to save automatically, uncheck "Auto save".<br>
If you want to save other than auto save, press "s" on the keyboard.<br>
<img src="https://user-images.githubusercontent.com/37477845/131691394-72adf13c-c4dc-4df3-b1b2-f33d38acf226.png" width="80%"><br><br>

### Other settings
<img src="https://user-images.githubusercontent.com/37477845/131691853-0ce525ee-34dc-4328-9978-2ee8903a4d8e.png" width="80%"><br>
* Mask alpha：Image Mask Superimpose Display Shading Degree
* Iteration：Number of iterations of the GrabCut algorithm
* Draw thickness：Line thickness when foreground / background is specified
* Output width：Width of output image
* Output height：Vertical width of output image

# ToDo
- [x] ~~Memory leak improvement~~
- [x] ~~Allows other than upper left → lower right drag when ROI is selected~~
- [x] ~~Show ROI selection when class ID is selected with a shortcut key~~

# Author
Kazuhito Takahashi(https://twitter.com/KzhtTkhs)
 
# License 
GrabCut-Annotation-Tool is under [Apache-2.0 License](LICENSE).

The sample image uses the photograph of [フリー素材 ぱくたそ](https://www.pakutaso.com).
