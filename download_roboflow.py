from roboflow import Roboflow

rf = Roboflow(api_key="o0SuCP8hmTiCHyyrBJXE")
project = rf.workspace("yolov5-epx0y").project("household-uhdlf")

# Tải về thư mục household_raw (đầy đủ 20 class)
dataset = project.version(1).download(
    "yolov11",
    location="D:/robot_aiot/household_raw"
)
print("Tải xong tại:", dataset.location)