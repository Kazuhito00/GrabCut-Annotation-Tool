[Japanese/[English](https://github.com/Kazuhito00/GrabCut-Annotation-Tool/blob/main/README_EN.md)]

# GrabCut-Annotation-Tool
https://user-images.githubusercontent.com/37477845/131681382-020df52c-dbc7-4750-80d1-42ff141ba829.mp4

OpenCVのGrabCut()を利用したアノテーションツールです。<br>
セマンティックセグメンテーション向けのデータセット作成にご使用いただけます。<br>
※GrabCutのアルゴリズムの都合上、境界がはっきりしているデータのアノテーションに向いています。<br>

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
ソースコードです。

#### input
アノテーション対象の画像ファイルを格納するディレクトリです。

#### output
アノテーション結果を保存するディレクトリです。
* image：リサイズした画像が格納されます
* annotation：アノテーション結果が格納されます<br>※パレットモードのPNG形式で保存

# Usage
次のコマンドで起動してください。
```
python app.py
```
起動時には以下オプションが指定可能です。
* --input<br>
入力画像格納パス<br>
デフォルト：input
* --output_image<br>
アノテーション結果(画像)の格納パス<br>
デフォルト：output/image
* --output_annotation<br>
アノテーション結果(セグメンテーション画像)の格納パス<br>
デフォルト：output/annotation
* --config<br>
ロードするコンフィグファイル<br>
デフォルト：config.json

# Using GrabCut-Annotation-Tool
### ファイル選択
ファイル一覧をクリックすることでアノテーション対象を切り替えることが出来ます。<br>
ショートカットキー　↑、p：上のファイルへ　↓、n：下のファイルへ<br>
<img src="https://user-images.githubusercontent.com/37477845/131686101-c94132bc-4b76-488a-85fe-69d9d9c216bd.png" width="80%">

### 初期ROI指定
「Select ROI」と表示されている時にマウス右ドラッグで初期ROIを指定できます。<br>
<img src="https://user-images.githubusercontent.com/37477845/131687291-4f4c06d5-89fa-452d-925f-5576edc5af64.png" width="80%"><br><br>

ドラッグ終了後、GrabCut処理が行われます。<br>
<img src="https://user-images.githubusercontent.com/37477845/131687690-295dc463-f82e-447b-86f8-65bbf6cf4e2d.png" width="80%"><br><br>

領域が選択されます。<br>
<img src="https://user-images.githubusercontent.com/37477845/131688127-3fc1c00e-0f99-435a-aa29-d9392c7af6d0.png" width="80%"><br><br>

### 後景指定
マウス右ドラッグで後景の指定が出来ます。<br>
<img src="https://user-images.githubusercontent.com/37477845/131688309-c47184d9-f793-49f0-aa26-445ea2c2b431.png" width="80%"><br><br>

<img src="https://user-images.githubusercontent.com/37477845/131688599-dc78e307-8a3b-4ec7-a9be-05325486ee5e.png" width="80%"><br><br>

### 前景指定
「Manually label background」のチェックを外すことで前景指定に切り替えることが出来ます<br>
ショートカットキー　Ctrl<br>
<img src="https://user-images.githubusercontent.com/37477845/131688947-ab0505ca-8413-4afe-8d5a-c42ae1f25a3f.png" width="80%"><br><br>

マウス右ドラッグで前景の指定が出来ます。<br>
<img src="https://user-images.githubusercontent.com/37477845/131689310-5447308d-2019-48d7-8a43-df7707969599.png" width="80%"><br><br>

<img src="https://user-images.githubusercontent.com/37477845/131689509-ea0597a4-939a-4821-a077-40720687e8b1.png" width="80%"><br><br>

### クラスID切り替え
Class IDのチェックボックスを押すことでクラスIDを切り替えることが出来ます。<br>
一桁のIDはショートカットキーでの切り替えも可能です。<br>
ショートカットキー　0-9<br>
<img src="https://user-images.githubusercontent.com/37477845/131690009-862e763d-9714-4420-bf9c-7185daa0bbff.png" width="80%"><br><br>

クラスID切り替え後はROI指定を行う必要があります。<br>
<img src="https://user-images.githubusercontent.com/37477845/131690463-667530d6-6e89-4eec-88ff-8a5aaf55a8a1.png" width="80%"><br><br>

<img src="https://user-images.githubusercontent.com/37477845/131690674-293340bc-eedb-48dc-9a20-8a5e4e61d1db.png" width="80%"><br><br>

### 自動保存
リサイズ画像とアノテーション画像はGrabCut処理毎に自動保存されます。<br>
<img src="https://user-images.githubusercontent.com/37477845/131691035-ab98cf83-f659-4efe-89aa-896badcee985.png" width="50%"><br><br>

自動保存をしたくない場合は「Auto save」のチェックを外してください。<br>
自動保存以外で保存したい場合は、キーボード「s」を押してください。<br>
<img src="https://user-images.githubusercontent.com/37477845/131691394-72adf13c-c4dc-4df3-b1b2-f33d38acf226.png" width="80%"><br><br>

### その他設定
<img src="https://user-images.githubusercontent.com/37477845/131691853-0ce525ee-34dc-4328-9978-2ee8903a4d8e.png" width="80%"><br>
* Mask alpha：画像のマスク重畳表示の濃淡具合
* Iteration：GrabCutアルゴリズムのイテレーション回数
* Draw thickness：前景/後景指定時の線の太さ
* Output width：出力画像の横幅
* Output height：出力画像の縦幅

# ToDo
- [x] ~~メモリリーク対策~~
- [ ] ROI選択時に左上→右下ドラッグ以外も可能にする
- [ ] クラスIDをショートカットキーで選択した際にROI選択表示にする

# Author
高橋かずひと(https://twitter.com/KzhtTkhs)
 
# License 
GrabCut-Annotation-Tool is under [Apache-2.0 License](LICENSE).

サンプル画像は[フリー素材ぱくたそ](https://www.pakutaso.com)様の写真を利用しています。
