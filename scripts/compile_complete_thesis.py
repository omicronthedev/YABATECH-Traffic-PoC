import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

out_dir = Path(r"c:\Users\User\yabatech-traffic-poc\outputs")
fig_dir = out_dir / "figures"
target_docx = out_dir / "YABATECH_Adaptive_Traffic_PoC_Chapters_1_to_3.docx"

doc = Document()

# Set standard 1-inch margins
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# Helper styling functions
def format_run(run, text, font_name="Times New Roman", size_pt=12, bold=False, italic=False, color=None):
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color

def add_para(doc, text="", style='Normal', align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, line_spacing=1.5):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        r = p.add_run(text)
        format_run(r, text)
    return p

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    format_run(r, text, size_pt=14, bold=True)
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    format_run(r, text, size_pt=12.5, bold=True)
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    format_run(r, text, size_pt=12, bold=True, italic=True)
    return p

def add_def_item(doc, term, definition):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    r1 = p.add_run(term)
    format_run(r1, term, bold=True)
    r2 = p.add_run(definition)
    format_run(r2, definition)

def add_figure_image(doc, img_path, caption_text, width_inches=6.2):
    if img_path.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(str(img_path), width=Inches(width_inches))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(12)
        r_cap = p_cap.add_run(caption_text)
        format_run(r_cap, caption_text, size_pt=11, bold=True, italic=True)

# ============================================================================
# TITLE PAGE
# ============================================================================
p = add_para(doc, "YABA COLLEGE OF TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
r = p.runs[0]; format_run(r, "YABA COLLEGE OF TECHNOLOGY", size_pt=14, bold=True)

p = add_para(doc, "SCHOOL OF TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
r = p.runs[0]; format_run(r, "SCHOOL OF TECHNOLOGY", size_pt=13, bold=True)

p = add_para(doc, "DEPARTMENT OF COMPUTER TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
r = p.runs[0]; format_run(r, "DEPARTMENT OF COMPUTER TECHNOLOGY", size_pt=13, bold=True)

p = add_para(doc, "A PROJECT REPORT SUBMITTED TO THE DEPARTMENT OF COMPUTER TECHNOLOGY,\nSCHOOL OF TECHNOLOGY, YABA COLLEGE OF TECHNOLOGY,\nIN PARTIAL FULFILMENT OF THE REQUIREMENTS FOR THE AWARD OF\nTHE HIGHER NATIONAL DIPLOMA (HND) IN COMPUTER TECHNOLOGY", 
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
r = p.runs[0]; format_run(r, p.text, size_pt=11, italic=True)

p = add_para(doc, "ADAPTIVE TRAFFIC SIGNAL CONTROL USING REAL-TIME COMPUTER VISION AND VEHICLE QUEUE ESTIMATION: A PROOF-OF-CONCEPT FOR THE YABATECH FRONT GATE INTERSECTION", 
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
r = p.runs[0]; format_run(r, p.text, size_pt=14, bold=True)

p = add_para(doc, "BY", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
r = p.runs[0]; format_run(r, "BY", size_pt=12, bold=True)

# Table of Students
students = [
    ("1", "LAWAL PRINCE IFEMIDE", "F/HD/24/3211115"),
    ("2", "OLATUNJI TAIWO WASIU", "F/HD/24/3211009"),
    ("3", "OYEWOLE AFEEZ ISREAL", "F/HD/24/3211020"),
    ("4", "SHOWUNMI OLAMILEKAN SODIQ", "F/HD/24/3211123"),
    ("5", "OKOLI CHINONYE GERALDINE", "F/HD/24/3211062"),
    ("6", "SALAMI JOSHUA A.", "F/HD/24/3211007"),
    ("7", "AMAMCHUKWU IKECHUKWU TIMOTHY", "F/HD/24/3211129"),
]

table = doc.add_table(rows=1, cols=3)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr_cells = table.rows[0].cells
hdr_cells[0].text = "S/N"
hdr_cells[1].text = "NAME"
hdr_cells[2].text = "MATRIC NUMBER"
for c in hdr_cells:
    for p in c.paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            format_run(r, r.text, size_pt=10, bold=True)

for sn, name, mat in students:
    row_cells = table.add_row().cells
    row_cells[0].text = sn
    row_cells[1].text = name
    row_cells[2].text = mat
    for idx, c in enumerate(row_cells):
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                format_run(r, r.text, size_pt=10)

add_para(doc, "", space_after=12)

p = add_para(doc, "PROGRAMME: HIGHER NATIONAL DIPLOMA (HND), COMPUTER TECHNOLOGY", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
r = p.runs[0]; format_run(r, p.text, size_pt=11, bold=True)

p = add_para(doc, "SUPERVISOR: MR. OLUDIPE O.", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
r = p.runs[0]; format_run(r, p.text, size_pt=12, bold=True)

p = add_para(doc, "NOVEMBER, 2026", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
r = p.runs[0]; format_run(r, p.text, size_pt=12, bold=True)

doc.add_page_break()

# ============================================================================
# SUMMARY OF THE PROPOSED STUDY
# ============================================================================
add_heading_1(doc, "SUMMARY OF THE PROPOSED STUDY")

add_para(doc, "Traffic congestion is one of the most persistent problems in Lagos. Commuters lose hours on the road, businesses lose money, and ambulances and other emergency vehicles struggle to get through. One contributing factor is that many signals run on fixed timings. They give the same green time to a packed road and to an almost empty one, and they cannot react to what is happening at the junction.")

add_para(doc, "This study develops an adaptive traffic signal controller that takes a live camera feed, detects vehicles with a YOLO object detection model, and estimates the queue on each approach using regions of interest drawn on the video frame. From those queue counts, the system decides how much green time each approach should get. It is built as a proof-of-concept and tested at the intersection in front of the Yaba College of Technology (YABATECH) Front Gate on Hussey Road, Yaba, Lagos State.")

add_para(doc, "The aim is to design, implement and evaluate this controller for the selected intersection. The study follows the Design Science Research approach. Observation and video recording from several viewpoints at the junction provide the data on current traffic behaviour, and the system is built iteratively in Python with the Ultralytics YOLO framework, OpenCV and NumPy. For evaluation, the controller is run on the recorded video and the signal phases it produces are compared with those a fixed-time controller would have produced for the same traffic.")

add_para(doc, "The study tests whether a camera-based controller can respond to real traffic conditions at a Lagos junction without embedded road sensors. If it can, the prototype gives a starting point for other locations.")

doc.add_page_break()

# ============================================================================
# TABLE OF CONTENTS
# ============================================================================
add_heading_1(doc, "TABLE OF CONTENTS")

toc_items = [
    ("Summary of the Proposed Study", "ii"),
    ("Table of Contents", "iii"),
    ("List of Figures", "v"),
    ("List of Abbreviations", "vi"),
    ("CHAPTER ONE: INTRODUCTION", "1"),
    ("1.1  Background to the Study", "1"),
    ("1.2  Statement of the Problem", "2"),
    ("1.3  Aim of the Study", "3"),
    ("1.4  Objectives of the Study", "3"),
    ("1.5  Research Questions", "4"),
    ("1.6  Research Hypotheses", "4"),
    ("1.7  Significance of the Study", "4"),
    ("1.8  Scope of the Study", "5"),
    ("1.9  Overview of the Research Methodology", "5"),
    ("1.10  Definition of Terms", "6"),
    ("CHAPTER TWO: LITERATURE REVIEW", "8"),
    ("2.1  Introduction", "8"),
    ("2.2  Traffic Signal Control", "8"),
    ("2.2.1  Types of Traffic Signal Control", "8"),
    ("2.2.2  Impact of Traffic Signal Control", "9"),
    ("2.2.3  Vehicle Detection for Traffic Signal Control", "10"),
    ("2.3  Computer Vision and Object Detection", "10"),
    ("2.3.1  Types of Object Detection Methods", "11"),
    ("2.3.2  Applications of Computer Vision in Road Traffic", "11"),
    ("2.3.3  Computer Vision for Adaptive Traffic Signal Control", "12"),
    ("2.3.4  Computer Vision Techniques for Adaptive Signal Control", "12"),
    ("2.4  Review of Related Studies", "13"),
    ("2.5  Summary of Related Literature", "15"),
    ("2.6  Conclusion", "16"),
    ("CHAPTER THREE: METHODOLOGY", "17"),
    ("3.1  Introduction", "17"),
    ("3.2  Research Design", "17"),
    ("3.3  Study Area", "18"),
    ("3.4  Population of the Study", "19"),
    ("3.5  Sample Size", "20"),
    ("3.6  Sampling Technique", "21"),
    ("3.7  Sources of Data", "21"),
    ("3.8  Methods of Data Collection", "22"),
    ("3.9  Research Instruments", "23"),
    ("3.10  Validity and Reliability", "24"),
    ("3.11  Analysis of the Existing System", "25"),
    ("3.12  Design of the Proposed Solution", "26"),
    ("3.13  Development/Implementation Methodology", "29"),
    ("3.14  Hardware Requirements", "30"),
    ("3.15  Software Requirements", "31"),
    ("3.16  Proposed Implementation Procedure", "31"),
    ("3.17  Method of Data Analysis", "33"),
    ("3.18  Proposed Testing and Validation", "34"),
    ("REFERENCES", "36"),
]

for title, page in toc_items:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    is_ch = title.startswith("CHAPTER") or title.isupper()
    r1 = p.add_run(title)
    format_run(r1, title, bold=is_ch)
    r2 = p.add_run(f"\t{page}")
    format_run(r2, f"\t{page}", bold=is_ch)

doc.add_page_break()

# ============================================================================
# LIST OF FIGURES & LIST OF ABBREVIATIONS
# ============================================================================
add_heading_1(doc, "LIST OF FIGURES")

figures = [
    ("Figure 3.1", "High-Level System Architecture"),
    ("Figure 3.2", "Level 0 Context Diagram of the Adaptive Traffic Signal Control System"),
    ("Figure 3.3", "Level 1 Data Flow Diagram of the Adaptive Traffic Signal Control System"),
]

for fnum, ftitle in figures:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run(f"{fnum}  ")
    format_run(r1, f"{fnum}  ", bold=True)
    r2 = p.add_run(ftitle)
    format_run(r2, ftitle)

add_heading_1(doc, "LIST OF ABBREVIATIONS")

abbrs = [
    ("CNN", "Convolutional Neural Network"),
    ("DFD", "Data Flow Diagram"),
    ("DSR", "Design Science Research"),
    ("FHWA", "Federal Highway Administration"),
    ("FPS", "Frames Per Second"),
    ("FSM", "Finite State Machine"),
    ("HND", "Higher National Diploma"),
    ("HUD", "Head-Up Display"),
    ("ITS", "Intelligent Transport Systems"),
    ("LASTMA", "Lagos State Traffic Management Authority"),
    ("MJPEG", "Motion Joint Photographic Experts Group"),
    ("OpenCV", "Open Source Computer Vision Library"),
    ("PCU", "Passenger Car Unit"),
    ("ROI", "Region of Interest"),
    ("RTSP", "Real-Time Streaming Protocol"),
    ("TRL", "Transport Research Laboratory"),
    ("YABATECH", "Yaba College of Technology"),
    ("YOLO", "You Only Look Once"),
]

for ab, meaning in abbrs:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(ab)
    format_run(r1, ab, bold=True)
    r2 = p.add_run(f"\t{meaning}")
    format_run(r2, f"\t{meaning}")

doc.add_page_break()

# ============================================================================
# CHAPTER ONE
# ============================================================================
add_heading_1(doc, "CHAPTER ONE\nINTRODUCTION")

add_heading_2(doc, "1.1  Background to the Study")
add_para(doc, "Roads are how most people and goods move through a city, and they come under more strain as the city grows. The United Nations (2018) reports that more than half of the world's population now lives in urban areas, and that share is still rising. More people means more vehicles and more trips, and many junctions now carry far more traffic than they were built for.")
add_para(doc, "Signals are one of the main tools for managing that load. The traditional kind runs on fixed timing: each direction gets a set number of seconds of green, whatever the traffic looks like at that moment. This works well enough when flow is steady, but it wastes time when one road is packed and another is nearly empty. Many cities have therefore moved to adaptive signal control, in which sensors detect vehicles and the timing adjusts as conditions change. Field studies reviewed by the United States Department of Transportation (2015) report travel time reductions of up to about 29 per cent after adaptive systems were installed, though results vary considerably between sites.")
add_para(doc, "Lagos shows why this matters. It has an estimated population of over 20 million, making it the most populous city in Nigeria and one of the largest in Africa. The Danne Institute for Research (2021) estimated that Lagos residents spend an average of 2.21 hours a day in traffic on their way to work, with an economic loss to the state of about ₦4 trillion a year. Some of these figures have been disputed, but anyone who has sat in rush-hour traffic on a Lagos road will not doubt the scale of the problem.")
add_para(doc, "The Lagos State Government has tried several measures. These include traffic officers from the Lagos State Traffic Management Authority (LASTMA), bus rapid transit lanes and plans to expand water transport. They help, but they either add capacity or put people on the road to direct vehicles by hand. None of them gives the signals themselves any ability to respond to the traffic in front of them.")
add_para(doc, "Advances in computer vision and deep learning offer a cheaper alternative. Object detection models such as YOLO (You Only Look Once), introduced by Redmon, Divvala, Girshick and Farhadi (2016) and refined through several versions since, can identify and count vehicles in video in real time, even on modest hardware. Pair that with a live camera feed, which can now come from an ordinary smartphone, and the number of vehicles queued on each approach can be estimated without putting any sensors in the road. Those estimates can then drive a timing algorithm that gives more green to the busier approach and less to the quieter one.")
add_para(doc, "This study builds a proof-of-concept controller along those lines. It uses a live camera stream, YOLO detection and region-of-interest queue estimation to control signal phases at a real Lagos intersection: the junction in front of the YABATECH Front Gate on Hussey Road, Yaba. Hussey Road meets Alakija Street and the campus entrance there, and the junction handles cars, buses, tricycles (keke) and motorcycles at all hours. Whether a system of this kind can cope with that mix of vehicles is what the study sets out to find out.")

add_heading_2(doc, "1.2  Statement of the Problem")
add_para(doc, "The problem this study addresses is that traffic signals at many Lagos junctions, including the YABATECH Front Gate intersection on Hussey Road, cannot respond to how much traffic is actually on the road. From what can be observed at the study junction, traffic officers or the drivers themselves, informally, are the only form of control. The result is long queues on busy approaches while green time is wasted on roads with few vehicles.")
add_para(doc, "Commuters, including the thousands of students and staff who pass through the YABATECH gate daily, lose time and spend more on fuel; the Danne Institute for Research (2021) puts the average time Lagosians spend in traffic at 2.21 hours daily. Traffic officers have no data to work from and can only react once a jam has formed. Government agencies have no reliable, continuous record of traffic volumes at the junction, so planning decisions rest on limited information.")
add_para(doc, "Conventional adaptive systems depend on embedded road sensors such as inductive loops, magnetometers or radar units. These are expensive to install and maintain, particularly in a developing-country setting where road surfaces are frequently disrupted. That cost has kept adaptive signal control out of many Lagos junctions.")
add_para(doc, "The gap this study addresses, then, is the lack of a vision-based signal controller that uses a camera and deep-learning vehicle detection to adjust timing to real traffic conditions, with no embedded road sensors.")

add_heading_2(doc, "1.3  Aim of the Study")
add_para(doc, "The aim of this study is to design, implement, and evaluate a proof-of-concept adaptive traffic signal control system that uses real-time computer vision and vehicle queue estimation from a live camera feed to adjust signal timing at the YABATECH Front Gate intersection on Hussey Road, Yaba, Lagos State.")

add_heading_2(doc, "1.4  Objectives of the Study")
add_para(doc, "To achieve this aim, the study will:")
objectives = [
    "1. Examine how traffic is currently managed at the YABATECH Front Gate intersection and the problems faced by road users and any traffic officers deployed there.",
    "2. Design a system architecture that captures a live video stream from a camera, detects and counts vehicles using the YOLO object detection model, and estimates the queue length on each approach of the junction using region-of-interest polygons.",
    "3. Develop an adaptive signal timing algorithm that adjusts the green time of each approach based on the number of vehicles currently queued, with appropriate safety intervals (yellow and all-red clearance phases).",
    "4. Implement the system as a working proof-of-concept in Python, using OpenCV for video capture, the Ultralytics YOLO framework for vehicle detection, and a state-machine signal controller.",
    "5. Evaluate the system by running it on recorded intersection video from multiple viewpoints and analysing the resulting signal phase distributions, queue response behaviour, and processing throughput."
]
for obj in objectives:
    add_para(doc, obj)

add_heading_2(doc, "1.5  Research Questions")
add_para(doc, "The research questions follow from the objectives above:")
questions = [
    "1. How is traffic currently managed at the YABATECH Front Gate intersection, and what are the main problems observed?",
    "2. What system architecture can capture a live camera feed, detect vehicles using deep learning, and estimate queue lengths on each approach?",
    "3. How can signal timing be adjusted automatically based on the number of vehicles queued on each approach, while maintaining safe clearance intervals?",
    "4. Can a proof-of-concept implementation running on consumer-grade hardware process a live video stream fast enough to make timely signal decisions?",
    "5. To what extent does the adaptive timing respond appropriately to changing traffic conditions compared with a fixed-time signal plan?"
]
for q in questions:
    add_para(doc, q)

add_heading_2(doc, "1.6  Research Hypotheses")
add_para(doc, "The evaluation compares the adaptive controller with a fixed-time plan under the same traffic conditions, so a single pair of hypotheses is stated:")
add_para(doc, "H₀: There is no significant difference in signal responsiveness (measured by the proportion of green time allocated to the busier approach) between fixed-time signal control and the proposed vision-based adaptive control.")
add_para(doc, "H₁: The proposed vision-based adaptive control allocates a significantly higher proportion of green time to the busier approach than fixed-time signal control does.")

add_heading_2(doc, "1.7  Significance of the Study")
add_para(doc, "Traffic management agencies such as LASTMA stand to gain the most. The study shows whether adaptive signal control can be done with a camera and open-source software, without the capital cost of embedded sensors. If it works, it offers a cheaper route to upgrading signal control at Lagos junctions than conventional sensor-based systems.")
add_para(doc, "Road users who pass through the YABATECH Front Gate intersection every day, including commuters, students, staff and commercial drivers, would benefit from signal timing that follows actual demand. Even modest improvements in green-time allocation at a busy junction can reduce idling and fuel use.")
add_para(doc, "Planners and policymakers would get evidence on whether camera-based vehicle detection is accurate and fast enough for real-time signal control in Lagos conditions, where cars, buses, tricycles and motorcycles share the road, often with poor road surfaces and lighting.")
add_para(doc, "For the academic community, the study documents a reproducible example of pairing YOLO object detection with an adaptive timing algorithm in a working prototype. The code, data and method are described in enough detail for other students and researchers to adapt and improve.")

add_heading_2(doc, "1.8  Scope of the Study")
add_para(doc, "The study covers the design and implementation of a proof-of-concept adaptive signal controller. This includes capturing a live video stream from a camera, detecting and counting vehicles with YOLO, estimating queue lengths on each approach with region-of-interest polygons, and running a timing algorithm with green, yellow and all-red phases. It does not cover installing signal hardware, number-plate recognition, speed enforcement, fines or any other law enforcement.")
add_para(doc, "Geographically, the study is limited to the intersection in front of the YABATECH Front Gate on Hussey Road, Yaba, Lagos State, where Hussey Road meets Alakija Street and the campus entrance. The road runs west past the WAEC Building and the 68 Nigerian Army Reference Hospital (Military Hospital, Yaba) toward the Federal Science and Technical College (FSTC) Yaba, and east toward Higher College Road and the junction at the Jibowu Pedestrian Bridge. The design could be extended to other junctions, but only this one is tested here.")
add_para(doc, "The system processes one camera viewpoint at a time and controls the phases for the approaches visible from that viewpoint. It does not fuse several cameras to cover all approaches at once, although the architecture would allow that extension. The prototype runs on a standard laptop without a dedicated GPU, using CPU-based inference. The work runs from requirements gathering through design, implementation and testing, within the time allowed for the project.")

add_heading_2(doc, "1.9  Overview of the Research Methodology")
add_para(doc, "The study follows the Design Science Research (DSR) approach, which suits projects whose main output is a working artefact (Hevner, March, Park and Ram, 2004). Observation at the junction, including video recording from several viewpoints, provides the primary data on traffic flow, vehicle types and queue behaviour. Secondary data comes from journal articles, government reports and earlier work on adaptive traffic control and vehicle detection.")
add_para(doc, "The system is built iteratively in Python. Ultralytics YOLO handles vehicle detection, OpenCV handles video capture and display, and NumPy supports the geometry behind region-of-interest queue estimation. The timing algorithm is a finite-state machine with configurable minimum and maximum green time, time per vehicle, yellow duration and all-red clearance. A setup mode lets the user define the approach zone polygons for any camera viewpoint by clicking on the video frame.")
add_para(doc, "For evaluation, the system is run on recorded video of the intersection from several viewpoints. The metrics collected are vehicles detected per frame, queue count on each approach at each phase transition, green time allocated to each approach, number of phase transitions, and processing speed in frames per second. These are compared with what a fixed-time controller would do with the same traffic input. Chapter Three explains the method in full.")

add_heading_2(doc, "1.10  Definition of Terms")
definitions = [
    ("Adaptive Traffic Signal Control:  ", "In this study, a system that adjusts the green time given to each approach of a junction based on the number of vehicles currently detected, instead of following a fixed schedule."),
    ("Computer Vision:  ", "Algorithms that extract information from images or video, here used to detect and count vehicles."),
    ("YOLO (You Only Look Once):  ", "A family of deep-learning object detection models that can identify and locate multiple objects in a single image in one forward pass through the network, enabling real-time detection."),
    ("Region of Interest (ROI):  ", "A user-defined polygonal area in the camera frame that corresponds to a particular approach of the junction. Vehicles detected within this polygon are counted as part of that approach's queue."),
    ("Queue Estimation:  ", "The process of counting the number of vehicles within an approach zone at a given moment, used as the input to the signal timing algorithm."),
    ("Fixed-Time Signal:  ", "A traffic light that gives each direction the same preset green time in every cycle, regardless of actual traffic conditions."),
    ("Green Time:  ", "The number of seconds a signal stays green for one direction during a single phase."),
    ("Phase:  ", "One step in the signal cycle during which a particular approach receives a green signal while other approaches are held at red."),
    ("All-Red Clearance:  ", "A short interval (typically two to three seconds) during which all approaches show a red signal, allowing vehicles already in the junction to clear before the next phase begins."),
    ("Gap-Out:  ", "A mechanism in the adaptive controller that ends a green phase early if the queue on the active approach clears while other approaches have waiting traffic, rather than holding green for the full allocated time."),
    ("Livestream Feed:  ", "A continuous video signal transmitted in real time from a camera (in this study, a smartphone camera) to the processing system over a network connection."),
    ("Frames Per Second (FPS):  ", "The number of video frames the system can process per second, indicating the speed of detection and decision-making.")
]
for term, definition in definitions:
    add_def_item(doc, term, definition)

doc.add_page_break()

# ============================================================================
# CHAPTER TWO
# ============================================================================
add_heading_1(doc, "CHAPTER TWO\nLITERATURE REVIEW")

add_heading_2(doc, "2.1  Introduction")
add_para(doc, "This chapter reviews traffic signal control, computer vision, vehicle detection and traffic simulation. It discusses fixed-time, vehicle-actuated and adaptive signal strategies, and examines how vehicle information can be detected, classified and tracked to support signal decisions. Attention is given to wide-angle camera views, mixed traffic and the separate gate exit at the Yaba College of Technology (YABATECH) junction.")
add_para(doc, "This project is specifically a simulated traffic-control system, not a physical installation at the junction. The road layout, traffic movements, camera view, detection zones and signal operation will be represented in a virtual environment. The simulation will provide a controlled and repeatable setting for examining the proposed controller and comparing it with a fixed-time alternative. It will not, on its own, demonstrate performance on a real road or prove actual reductions in congestion, delay or accidents.")
add_para(doc, "The review distinguishes findings reported by previous studies from outcomes that this project intends to test. It considers the local mix of kekes, danfos, okadas and private cars, the college gate exit, a proposed fisheye camera view and virtual detection zones. These topics form the basis for the simulation design discussed in Chapter Three.")

add_heading_2(doc, "2.2  Traffic Signal Control")
add_para(doc, "Traffic signal control manages conflicting movements by assigning right of way at different times. A phase serves one or more compatible movements, while a cycle is the complete sequence of phases. Green permits movement, amber warns that green is ending, and red requires traffic to stop. Clearance intervals separate conflicting movements (Koonce et al., 2008).")
add_para(doc, "Minimum green provides time for queued vehicles to begin moving, while maximum green limits how long one movement can continue at the expense of others. Clearance time is distinct from green service time and should be represented during phase transitions (Koonce et al., 2008). The model will represent Alakija Street, Hussey Road, the fence road and the college gate exit as separate phases. Their timing and selection will be tested under different simulated demand patterns.")

add_heading_3(doc, "2.2.1  Types of Traffic Signal Control")
add_para(doc, "Fixed-time, or pretimed, control operates using predetermined phase durations and a repeating schedule. It does not require vehicle detectors, but cannot automatically respond when demand changes or an approach is empty (Koonce et al., 2008). In this project, fixed-time control provides a baseline. The same simulated vehicle-arrival patterns can be replayed under fixed-time and adaptive control so that comparisons are made under consistent conditions.")
add_para(doc, "Webster’s method calculates fixed-time settings intended to minimise delay. The optimum cycle expression given by Webster (1958) and reproduced in TRL (1996) is:")
p = add_para(doc, "C₀ = (1.5L + 5) / (1 − Y)", align=WD_ALIGN_PARAGRAPH.CENTER)
r = p.runs[0]; format_run(r, p.text, bold=True)
add_para(doc, "where C₀ is the optimum cycle length in seconds, L is the total lost time per cycle in seconds, and Y is the sum of the critical flow ratios. Each ratio relates traffic flow to saturation flow. The expression can guide the comparison timing plan, but it depends on suitable traffic inputs. In a simulation, assumptions about arrival rates, vehicle mix and flow must be documented so that test runs can be repeated.")
add_para(doc, "Vehicle-actuated control uses detector calls to determine or extend signal timing. A phase may remain green while demand continues, subject to a termination condition or maximum green. The maximum prevents a persistent call from holding service indefinitely (Koonce et al., 2008). TRL (1996) also describes stages served in order, with empty stages omitted. These behaviours can be represented in software and tested with scripted vehicle arrivals and queue conditions.")
add_para(doc, "Adaptive control responds to current traffic information. SCOOT makes frequent small timing changes using detector information (Hunt et al., 1981), while SCATS also uses computer-based adaptive control (Sims and Dobinson, 1980). Their reported improvements come from their own trials and are not expected results for this project. The proposed controller will be evaluated using its own simulated scenarios and performance measures.")
add_para(doc, "The proposed system combines timing limits with demand-based phase selection. Simulated or camera-derived vehicle information will be used to estimate approach demand. Approaches with no demand may be skipped, and the next phase will be selected using the controller’s demand rule. The simulation can test low, moderate and heavy traffic, uneven arrivals, empty approaches, gate-exit demand and simultaneous queues. Findings will describe the model’s behaviour rather than claim real-road effectiveness.")

add_heading_3(doc, "2.2.2  Impact of Traffic Signal Control")
add_para(doc, "Traffic signals can organise conflicting movements and provide a more predictable sequence, but their benefits depend on location, timing, visibility, compliance and maintenance. TRL (1996) notes that poorly located or timed signals can increase delay and accidents, while unnecessary red periods may encourage drivers to disregard signals. At unsignalised junctions, informal “popular control” may occur when drivers negotiate priority through vehicle size, horn use or perceived urgency. The YABATECH gate junction provides a local setting for examining how competing movements can be represented in a model.")
add_para(doc, "Literature describes congestion in Lagos as involving commercial minibuses, motorcycles and pedestrians sharing road space (Kumar and Barrett, 2008). Public statements cited in the original project discuss the wider economic and time costs of congestion (Akoni, 2025), while reports have addressed gridlock associated with damaged traffic lights (Akomolafe and Jeariogbe, 2020). These reports provide context; they are not measurements of this junction and will not be treated as simulation findings.")
add_para(doc, "In this study, the effects of signal control will be examined as simulated outcomes. Indicators may include average vehicle delay, maximum waiting time, queue length, throughput and gate-exit waiting. The model can reveal how the programmed rules respond when demand changes or one approach becomes heavily loaded. Comparing adaptive and fixed-time control using identical traffic inputs allows a structured assessment. Simulation alone cannot prove that real drivers will behave the same way, that accidents will decrease, or that actual congestion will improve.")
add_para(doc, "Power reliability is also a practical concern. Reuters (2024) reported recurring electricity-grid interruptions in Nigeria, which highlights the need for backup power in field designs. Solar and battery supply may be discussed as part of the proposed concept, but the simulation will not establish battery endurance, energy generation or electrical reliability unless those factors are specifically modelled.")

add_heading_3(doc, "2.2.3  Vehicle Detection for Traffic Signal Control")
add_para(doc, "Detectors provide information to responsive controllers. Detector location affects whether the controller observes vehicles near the stop line or farther upstream. SCATS uses inductive loops near stop lines, as described by TRL (1996), while SCOOT uses upstream detector information (Hunt et al., 1981). These examples show that detection placement influences the information available about arriving traffic and queues.")
add_para(doc, "TRL (1996) discusses the importance of detector availability and maintenance. Koonce et al. (2008) explain that detector faults can create persistent calls, making maximum-green limits important. In a simulation, faults can be introduced as controlled test conditions—for example, a missed detection, a continuous false call or an inaccurate count. Such tests can reveal how the programmed controller responds and whether a fallback mode is correctly implemented.")
add_para(doc, "Video sensors can observe multiple road users and may provide vehicle counts, classes, queues and turning movements (Kastrinaki, Zervakis and Kalaitzakis, 2003). The virtual camera and detection zones will represent this approach. Detection inputs may be generated from known simulated vehicle positions or produced by running a detector on rendered simulation frames. These methods must be distinguished: emulated detection can test signal-control logic, but it does not measure computer-vision accuracy.")

add_heading_2(doc, "2.3  Computer Vision and Object Detection")
add_para(doc, "Computer vision processes images to extract information about a scene. In traffic applications, it can identify vehicles, estimate their positions, classify their types and track movement. Object detection typically returns a class label, bounding box and confidence score. YOLO is a deep-learning detector that predicts object locations and classes in a single-stage process (Redmon et al., 2016).")
add_para(doc, "Detection and control are separate functions. A detector identifies vehicles in images; a tracker links observations of the same vehicle across frames; a zone component associates vehicles with approaches; and the controller uses the resulting demand to select phases. Representing these functions as separate components in the simulation will make testing and debugging easier. Incorrect decisions can be traced to vehicle identification, zone assignment, demand calculation or signal logic.")
add_para(doc, "Presence in an image does not always mean a vehicle is waiting to proceed. A keke parked near a stall or a vehicle outside an approach zone should not automatically count as queued demand. The model must define detection boundaries and the rules for assigning vehicles to approaches. A virtual scene may not reproduce all real-world occlusion, lighting, road-user or camera conditions.")

add_heading_3(doc, "2.3.1  Types of Object Detection Methods")
add_para(doc, "Kastrinaki, Zervakis and Kalaitzakis (2003) discuss classical traffic-video approaches including feature-driven, area-driven and model-based methods. Feature-driven methods use selected visual features, area-driven methods analyse image regions, and model-based methods compare observations with object representations. The review also considers static and moving cameras because camera movement changes how image information is interpreted.")
add_para(doc, "Background-based methods can separate moving foreground objects from a model of the road scene, while motion-based methods identify changes between frames. Movement alone is insufficient for signal demand because a vehicle waiting at a red signal may be stationary. The controller therefore needs a representation of queue occupancy and waiting vehicles, not simply moving-object detection.")
add_para(doc, "Deep-learning detectors learn patterns from labelled images. Redmon et al. (2016) describe YOLO as a one-stage detector that predicts bounding boxes and class probabilities. Detection errors, including missed vehicles or inaccurate boxes, may affect zone assignment. COCO provides pretrained object categories (Lin et al., 2014), but locally relevant classes may be under-represented. Akujobi et al. (2026) discuss the under-representation of kekes in common datasets, supporting the need to consider local classes when a detector is used.")
add_para(doc, "For a simulation project, the detection method must match the actual implementation. If virtual coordinates emulate detections, the project should call this simulated detection input rather than claim to train or validate a vision model. If rendered frames are processed by a detector, the report should identify the model, classes, images and evaluation method.")

add_heading_3(doc, "2.3.2  Applications of Computer Vision in Road Traffic")
add_para(doc, "Computer vision has been applied to traffic counting and vehicle classification. Ajayi and Olusina (2024) developed roadside-video software that counted and classified vehicles crossing a detection line, displayed results and stored counts. Video can also support queue monitoring and junction observation, depending on camera placement and processing capability.")
add_para(doc, "Fisheye cameras may cover multiple approaches from a single position, but image distortion can affect detection (Gochoo et al., 2023). Wei et al. (2018) used traffic-camera data in evaluating IntelliLight, illustrating the use of camera-derived information in traffic-control research. In this project, a virtual camera will help examine the visibility of junction approaches and the gate exit. The source of vehicle data supplied to the controller will be documented so that the computer-vision component is not overstated.")

add_heading_3(doc, "2.3.3  Computer Vision for Adaptive Traffic Signal Control")
add_para(doc, "Camera-based control can use virtual detection zones to represent areas from which vehicles contribute to approach demand. Unlike road-embedded sensors, image zones can be adjusted in software. In simulation, zone boundaries can be changed and the resulting vehicle counts and signal decisions observed. This applies the wide-area monitoring advantages discussed by Kastrinaki, Zervakis and Kalaitzakis (2003) to the proposed junction.")
add_para(doc, "Separate zones will represent Alakija Street, Hussey Road, the fence road and the college gate exit. The gate zone is important because departing vehicles may wait independently of the public-road approaches. Zone boundaries should exclude roadside loading or parking areas that are not part of the queue. A supplementary view may be considered if the main camera is obstructed; the report should state whether it is actually simulated or only proposed.")
add_para(doc, "Simulation allows camera coverage and zone logic to be examined without installing equipment. The virtual camera can be repositioned and vehicle paths varied to test zone membership. However, rendered scenes may not fully reproduce real fisheye distortion, weather, glare, darkness, occlusion or vibration. The simulation can help assess the proposed layout but cannot establish real-world detection reliability.")

add_heading_3(doc, "2.3.4  Computer Vision Techniques for Adaptive Signal Control")
add_para(doc, "YOLO-family models can detect and classify vehicles (Redmon et al., 2016). A multi-object tracker associates detections across frames so vehicles retain identities. SORT uses a Kalman filter for motion prediction and the Hungarian algorithm for association; Bewley et al. (2016) discuss how detection quality influences tracking. Persistent identities can help estimate how long vehicles remain in zones rather than treating each frame as a separate observation.")
add_para(doc, "Zone counting connects tracks to approaches. Akujobi et al. (2026) describe keke-aware detection, tracking and region-of-interest counting, while Gochoo et al. (2023) study fisheye imagery. These works support attention to local classes and wide-angle distortion, but their results do not guarantee equal performance in the proposed virtual junction or on real YABATECH footage.")
add_para(doc, "Passenger car unit (PCU) weighting expresses different vehicle classes using a common demand measure. TRL (1996) suggests weights of 0.3 for motorcycles, 0.5 for auto-rickshaws and 1.25 for minibuses under 20 passengers. These are provisionally adopted for okadas, kekes and danfos; cars use 1.0. These values are literature-based, not calibrated using local traffic measurements.")
add_para(doc, "Varaiya (2013) presents max-pressure control using queue information and establishes a stability result for the specific control method studied. That result cannot automatically be applied to a different controller using PCU weights and waiting-time adjustments. The proposed rule will be assessed through simulation; its maximum-wait priority is intended to reduce neglected approaches but is not a formal stability proof.")
add_para(doc, "Reinforcement learning is another adaptive approach. Wei et al. (2018) evaluated IntelliLight using traffic data and a learned policy. Its training and data requirements make an explicit rule-based controller more manageable for this project. The controller’s phase choices and timers can be logged and explained. SUMO is an established microscopic traffic simulator (Lopez et al., 2018), while Blender is selected here primarily for scene modelling, visualisation, vehicle movement, camera views and signal states. Blender should not be described as a validated traffic-flow simulator unless its traffic behaviour is implemented and checked.")

add_heading_2(doc, "2.4  Review of Related Studies")
add_para(doc, "Sims and Dobinson (1980) described Sydney’s SCAT adaptive system, now SCATS. Its initial arterial-road trial reported peak-period journey-time advantages of 35 to 39 percent compared with optimised fixed-time coordination. Stop-line loops supplied detector information, as described by TRL (1996). Its strength is operational road evidence. However, arterial coordination differs from an isolated institutional-gate junction, and loop-based detection does not provide the proposed local visual classification. The reported gains are background evidence, not predicted results for this simulation.")
add_para(doc, "Hunt et al. (1981) presented SCOOT, which uses upstream detectors and a computer for frequent small timing adjustments. Trials reported about 12 percent lower average delay than updated optimised fixed-time plans. This supports adaptive control, but its detector infrastructure differs from the proposed local camera-based model. The project will investigate demand-responsive control within a simplified simulation.")
add_para(doc, "Varaiya (2013) examined max-pressure control based on local queues and established throughput stability for that control law. The method demonstrates the value of queue-based decisions, but the guarantee does not apply automatically to the proposed PCU-weighted and waiting-time rule. It motivates evaluation rather than assumption of stability.")
add_para(doc, "Wei et al. (2018) evaluated IntelliLight, a deep-reinforcement-learning approach, using large-scale traffic-camera data. Their work illustrates data-driven signal policies. Training requirements and the difficulty of interpreting individual decisions make it less suitable for the scope of this project. A rule-based controller is easier to implement, inspect and compare in simulation.")
add_para(doc, "Gochoo et al. (2023) introduced FishEye8K and evaluated YOLO-family detectors on fisheye traffic imagery. The work directly addresses wide-angle distortion, but its dataset does not include the specific Nigerian vehicle mix required here. It supports the camera concept while highlighting local classes and viewing position as design issues.")
add_para(doc, "Ajayi and Olusina (2024) developed roadside-video software for vehicle classification and counting. Its reported results illustrate non-intrusive traffic measurement, but line-crossing counts do not directly provide waiting demand or signal phase selection. The proposed simulation will connect zone-based demand and waiting time to signal decisions without claiming to reproduce that study’s detection accuracy.")
add_para(doc, "Owoeye et al. (2025) linked YOLOv5 webcam processing to an Arduino Mega and LED signals. Their prototype demonstrates a connection between detection and signal actuation and reported reductions in waiting time. The prototype used camera views per approach and did not report the proposed PCU-weighted local classes. Its findings are useful for comparison but cannot be transferred without testing.")
add_para(doc, "Akujobi et al. (2026) combined fine-tuned YOLO detectors with tracking and region-of-interest counting. They reported YOLO11l mAP@0.5 of 0.766 overall and 0.772 for kekes, while noting variation in counting performance by direction and scene. This addresses local vehicle detection, but results from their data do not establish accuracy for the proposed virtual camera or any future camera at YABATECH.")

add_heading_2(doc, "2.5  Summary of Related Literature")
add_para(doc, "The reviewed literature shows the progression from fixed schedules to actuated and adaptive methods that respond to traffic information. SCATS and SCOOT demonstrate operational adaptive control, max-pressure research provides theoretical results for a specific queue-based method, and reinforcement-learning studies demonstrate data-driven signal policies. Video-based detection and counting show how camera information can support traffic observation, while fisheye research highlights distortion and the need to consider local vehicle classes.")
add_para(doc, "This project combines selected ideas in a simulation: a virtual representation of the YABATECH gate junction; a camera view covering public approaches and gate exit; zones for the four movements; vehicle-class weighting; waiting-time information; minimum and maximum green limits; clearance intervals; demand-based phase selection; and fixed-time comparison using the same simulated traffic. The contribution is to design and examine this combination for the selected junction, rather than claim that each technique is new.")
add_para(doc, "The literature gap is framed as evaluating the combined arrangement in a documented simulation. Adaptive and fixed-time modes should be tested using consistent traffic arrivals, vehicle classes, initial conditions and run durations. Evaluation measures may include average delay, maximum waiting time, queue length, throughput and gate-exit waiting. If detections are emulated from known virtual positions, the tests evaluate controller logic only; they must not be presented as detector precision, recall or F1-score. If image-based detection is implemented, it should be evaluated separately against labelled ground truth.")
add_para(doc, "Simulation limitations must guide interpretation. Results depend on assumptions about vehicle arrivals, speeds, acceleration, turning, spacing, driver response and signal compliance. A simplified virtual scene may not capture informal driving, pedestrians, roadside loading, weather, visibility or all traffic variations. The project can demonstrate the design, compare strategies under stated assumptions and identify promising behaviours, but it cannot establish field effectiveness, installation cost, safety improvement or guaranteed congestion reduction. Such claims require field trials, calibration and validation using real traffic data.")

# Table 2.1 Summary of Related Works
table2 = doc.add_table(rows=1, cols=5)
table2.alignment = WD_TABLE_ALIGNMENT.CENTER
t2_hdrs = table2.rows[0].cells
t2_hdrs[0].text = "Author/Year"
t2_hdrs[1].text = "Approach"
t2_hdrs[2].text = "Data/Detection"
t2_hdrs[3].text = "Strength"
t2_hdrs[4].text = "Limitation/Relevance"
for c in t2_hdrs:
    for p in c.paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            format_run(r, r.text, size_pt=9.5, bold=True)

lit_rows = [
    ("Sims & Dobinson (1980)", "SCAT adaptive control", "Stop-line loops", "Operational arterial-road trial", "Not local visual classes or gate service"),
    ("Hunt et al. (1981)", "SCOOT timing adjustments", "Upstream loops; online computer", "Compared with optimised fixed-time plans", "Infrastructure differs from proposed simulation"),
    ("Varaiya (2013)", "Max-pressure control", "Neighbouring-link queues", "Stability for its control law", "Proof does not automatically apply to project rule"),
    ("Wei et al. (2018)", "Deep reinforcement learning", "Traffic-camera data", "Data-based policy evaluation", "Training needs; less transparent decisions"),
    ("Gochoo et al. (2023)", "Fisheye benchmark", "Taiwanese fisheye imagery", "Wide-angle distortion studied", "No local keke/danfo classes"),
    ("Ajayi & Olusina (2024)", "Video counting/classification", "Roadside camera; detection line", "Non-intrusive measurement", "No signal control or waiting-demand allocation"),
    ("Owoeye et al. (2025)", "YOLO adaptive prototype", "Webcam; LED modules", "Detection connected to signal actuation", "No PCU weighting/local vehicle classes"),
    ("Akujobi et al. (2026)", "Keke-aware detection/counting", "Fine-tuned YOLO, tracking, ROI", "Recognises under-represented local class", "Scene-dependent counting; no gate-control design"),
]

for row in lit_rows:
    rc = table2.add_row().cells
    for i, val in enumerate(row):
        rc[i].text = val
        for p in rc[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                format_run(r, r.text, size_pt=8.5)

add_para(doc, "", space_after=8)

add_heading_2(doc, "2.6  Conclusion")
add_para(doc, "This chapter reviewed traffic signal control, vehicle detection, computer vision, adaptive signal techniques and related studies. The literature provides a basis for comparing fixed-time, actuated and adaptive control and for considering camera-based detection, vehicle tracking, virtual zones and PCU-weighted demand. It also identifies limitations including detector faults, image distortion, under-represented local vehicle classes and the difficulty of transferring findings from one junction or method to another.")
add_para(doc, "The project will apply these ideas to a virtual model of the YABATECH gate junction. The proposed controller will use simulated or explicitly implemented camera-derived information to estimate approach demand, account for waiting time, select phases and enforce timing safeguards. Adaptive control will be compared with fixed-time control under identical simulated traffic conditions. Chapter Three will describe the methodology, virtual junction, simulation assumptions, architecture, control logic and evaluation procedures. Conclusions will be limited to what the implemented model and test results support.")

doc.add_page_break()

# ============================================================================
# CHAPTER THREE
# ============================================================================
add_heading_1(doc, "CHAPTER THREE\nMETHODOLOGY")

add_heading_2(doc, "3.1  Introduction")
add_para(doc, "This chapter presents the research design, system architecture, mathematical formulations, and experimental procedures employed to develop and evaluate the adaptive traffic signal control proof-of-concept for the Yaba College of Technology (YABATECH) Front Gate intersection on Hussey Road, Yaba, Lagos.")
add_para(doc, "Conventional traffic management at major institutional junctions in Lagos relies either on fixed-time signal cycles or manual intervention by traffic wardens. Both mechanisms fail to adapt dynamically to instantaneous fluctuations in traffic density, leading to asymmetric queue buildup, excessive fuel consumption, and avoidable commuter delays. To overcome the high capital expenditure and maintenance liabilities associated with intrusive in-pavement inductive loops or radar sensors, this study formulates a non-intrusive, edge-computable methodology. The approach pairs live video ingestion from a commodity mobile camera sensor with real-time deep-learning vehicle detection (YOLO11), geometric region-of-interest (ROI) queue estimation, and an adaptive finite-state machine signal controller.")
add_para(doc, "The subsequent sections detail the empirical site characterization, data sampling frameworks, mathematical models for dynamic green-phase allocation and gap-out clearance, system architectural specifications, data flow diagrams, hardware/software requirements, and the statistical validation protocol against fixed-time baselines.")

add_heading_2(doc, "3.2  Research Design")
add_para(doc, "This study adopts the Design Science Research (DSR) methodology (Hevner, March, Park, & Ram, 2004; Peffers, Tuunanen, Rothenberger, & Chatterjee, 2007), integrated with an empirical, quantitative experimental evaluation framework. Design Science Research is uniquely suited to computing and engineering disciplines where the principal objective is the creation and rigorous evaluation of an innovative technological artifact designed to solve an identified operational problem.")
add_para(doc, "The research design is structured across six iterative stages:")
dsr_stages = [
    "1. Problem Identification and Motivation: Empirical characterization of traffic congestion, asymmetric queue accumulation, and signal rigidity at the YABATECH Front Gate intersection.",
    "2. Definition of the Solution Objectives: Specification of functional requirements for an edge-deployable, camera-based controller capable of sustaining real-time processing (>= 15 FPS on consumer-grade hardware), identifying diverse vehicle classes, dynamically computing approach-weighted green splits, and enforcing fail-safe clearance transitions.",
    "3. Artifact Design and Development: Engineering the multi-tiered system artifact comprising a threaded zero-latency video ingestion engine; a single-stage convolutional neural network object detector (YOLO11n); a 2D polygonal spatial analysis module executing point-in-polygon containment tests; a state-machine traffic signal controller enforcing dynamic green timing, gap-out extensions, and clearance intervals; and a high-visibility visual Head-Up Display (HUD) and empirical telemetry logging pipeline.",
    "4. Demonstration: Deploying the prototype on empirical multi-viewpoint video streams captured directly at the YABATECH Front Gate intersection under varying traffic conditions.",
    "5. Evaluation: Subjecting the system to comparative experimental testing against an optimized fixed-time signal baseline across identical traffic arrival distributions, measuring performance via queue dissipation rates, green-time utilization efficiency, and processing latency.",
    "6. Communication: Formal documentation of system models, architectural schematics, source code artifacts, and empirical findings for academic dissemination and municipal engineering transfer."
]
for stg in dsr_stages:
    add_para(doc, stg)

add_heading_2(doc, "3.3  Study Area")
add_para(doc, "The spatial focal point of this study is the multi-leg intersection situated directly in front of the Yaba College of Technology (YABATECH) Front Gate along Hussey Road, located in Yaba, Lagos Mainland Local Government Area, Lagos State (approximate coordinates: 6.5180° N, 3.3715° E).")
add_para(doc, "The intersection constitutes a critical, complex node within the tertiary education and commercial corridor of Yaba, characterized by four primary converging legs:")
legs = [
    "1. Northern Approach (YABATECH Campus Gate): The primary gateway to Nigeria's premier higher educational institution. Accommodates intense, pulsing pedestrian crossings combined with vehicular ingress and egress (staff vehicles, delivery trucks, institution shuttles, and visitor cars). The entry is framed by an architectural gatehouse with distinct inbound and outbound access lanes.",
    "2. Southern Approach (Alakija Street): A dense commercial and residential feeder street directly confronting the campus gate. This approach feeds a continuous stream of commercial tricycles (Keke NAPEP), commercial motorcycles (Okada), delivery vans, and local passenger cars attempting left- and right-turning maneuvers onto Hussey Road amidst dense curbside retail activity.",
    "3. Western Approach (Hussey Road West): A single-carriageway corridor extending westward past the West African Examinations Council (WAEC) National Office, proceeding past the 68 Nigerian Army Reference Hospital (Military Hospital, Yaba), and terminating at the main gate of the Federal Science and Technical College (FSTC), Yaba, with a secondary lateral link to Commercial Avenue.",
    "4. Eastern Approach (Hussey Road East): The high-volume arterial corridor linking Hussey Road eastward into Higher College Road, providing direct connectivity to the critical grade-separated junction at the Jibowu Pedestrian Bridge along the Ikorodu Road / Herbert Macaulay Way arterial interchange."
]
for leg in legs:
    add_para(doc, leg)
add_para(doc, "Traffic flow at this junction exhibits severe heterogeneity. The operational modal split comprises private passenger cars, high-occupancy commercial minibuses (Danfo), three-wheeled motorized tricycles (Keke), two-wheeled motorcycles (Okada), and medium rigid commercial delivery trucks. Surface water ponding during rainfall events, combined with informal curbside pick-up/drop-off stops by commercial operators, frequently restricts effective carriageway width, making dynamic, responsive signal regulation necessary.")

add_heading_2(doc, "3.4  Population of the Study")
add_para(doc, "In the context of Design Science Research and computational transportation engineering, the study population comprises:")
pops = [
    "1. Vehicular Traffic Stream: The entire aggregate volume of motorized transport units traversing the YABATECH Front Gate intersection throughout active daytime operational hours (07:00 to 19:00 West Africa Time).",
    "2. Vehicle Class Typologies: The complete set of discrete vehicle categories operating within the Lagos metropolitan road ecosystem, specifically: Class 1: Private passenger automobiles (sedans, hatchbacks, SUVs); Class 2: Commercial minibuses (Danfo); Class 3: Three-wheeled commercial motorized tricycles (Keke NAPEP); Class 4: Two-wheeled commercial motorcycles (Okada); Class 5: Medium and heavy commercial trucks and institutional buses.",
    "3. Digital Frame Stream: The total theoretical universe of discrete visual image frames capturable by high-definition optical surveillance perspectives across all weather, lighting, and congestion states at the intersection."
]
for p_item in pops:
    add_para(doc, p_item)

add_heading_2(doc, "3.5  Sample Size")
add_para(doc, "The empirical data corpus assembled for training, parameter calibration, and simulation evaluation comprises nine distinct high-definition video recordings totaling 47 minutes and 28 seconds of continuous visual footage captured across multiple spatial viewpoints at the study junction.")

# Table 3.1 Sample Videos
table3_1 = doc.add_table(rows=1, cols=6)
table3_1.alignment = WD_TABLE_ALIGNMENT.CENTER
t31_hdrs = table3_1.rows[0].cells
t31_hdrs[0].text = "Identifier"
t31_hdrs[1].text = "Perspective Description"
t31_hdrs[2].text = "Orientation"
t31_hdrs[3].text = "Resolution"
t31_hdrs[4].text = "Duration"
t31_hdrs[5].text = "Frames"
for c in t31_hdrs:
    for p in c.paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            format_run(r, r.text, size_pt=9.5, bold=True)

v_rows = [
    ("main_intersection.mp4", "Elevated primary vantage overlooking Hussey Rd & Gate", "Portrait", "1080x1920", "11m 30s", "20,700"),
    ("view_WA0025.mp4", "Westward approach toward WAEC / FSTC", "Landscape", "1920x1080", "03m 45s", "6,750"),
    ("view_WA0026.mp4", "Reverse westward approach, curb-level", "Landscape", "1920x1080", "02m 15s", "4,050"),
    ("view_WA0028.mp4", "Alakija Street confluence, southward", "Portrait", "1080x1920", "04m 10s", "7,500"),
    ("view_WA0029.mp4", "Eastward approach toward Higher College Rd", "Landscape", "1920x1080", "05m 12s", "9,360"),
    ("view_WA0030.mp4", "Diagonal intersection covering Gate archway", "Portrait", "1080x1920", "04m 50s", "8,700"),
    ("view_WA0031.mp4", "Wide view capturing Alakija & Hussey merge", "Portrait", "1080x1920", "06m 02s", "10,860"),
    ("view_WA0033.mp4", "Campus gatehouse entrance & pedestrian zone", "Landscape", "1920x1080", "07m 14s", "13,020"),
    ("aerial_reference.mp4", "Elevated bird's-eye reference overview", "Landscape", "1280x720", "02m 40s", "4,800"),
]

for v in v_rows:
    rc = table3_1.add_row().cells
    for i, val in enumerate(v):
        rc[i].text = val
        for p in rc[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in [2, 3, 4, 5] else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                format_run(r, r.text, size_pt=8.5)

add_para(doc, "", space_after=8)
add_para(doc, "For formal benchmark simulation and statistical hypothesis testing, a dedicated 360.0-second (6.0-minute) continuous temporal slice of main_intersection.mp4 was extracted, representing peak midday campus turnover (12:30 PM). This benchmark test processed 2,371 evaluated frames, encompassing 20 full adaptive signal phase transitions, generating 2,371 rows of high-resolution telemetry data.")

add_heading_2(doc, "3.6  Sampling Technique")
add_para(doc, "This study employed a stratified purposive sampling technique combined with systematic temporal interval sampling:")
add_para(doc, "1. Spatial Stratification: Vantage points were selected purposively to ensure geometric representation of both the primary bidirectional arterial flow along Hussey Road and the perpendicular conflicting feeder flows from Alakija Street and the YABATECH gatehouse.")
add_para(doc, "2. Temporal Stratification: Video acquisition was scheduled to sample three operational traffic regimes: Morning Peak Period (07:30 - 09:15) with heavy directional commuter inflow from Jibowu/Ikorodu Road; Midday Inter-Peak (12:00 - 14:00) with high turning movements, commercial loading, and intense pedestrian friction; and Evening Dispersal (16:30 - 18:30) with heavy outbound flow toward the Jibowu interchange.")
add_para(doc, "3. Camera Placement Geometry: Camera positioning adhered to strict photogrammetric criteria: an elevated mounting height of 3.5 to 5.0 meters with a downward pitch angle of 30° to 45°. This elevation minimizes longitudinal inter-vehicle occlusion, ensuring that following vehicles in a queue remain visually separable.")

add_heading_2(doc, "3.7  Sources of Data")
add_para(doc, "Primary data was obtained directly through field-level experimental collection, including continuous digital video recordings capturing live traffic operations at the YABATECH intersection across the defined sampling matrix; physical geometric measurements extracted from Google Earth satellite telemetry and on-site distance calibration (carriageway widths: Hussey Road ≈ 7.2 m; Alakija Street throat ≈ 6.0 m; Gate access throat ≈ 8.5 m); and manual tally counts of vehicle queue lengths and departure headways conducted on-site to validate computer-vision inference accuracy.")
add_para(doc, "Secondary data supported algorithmic benchmarking and model parameterization, including pre-trained convolutional neural network weights from the COCO benchmark repository (Lin et al., 2014); Passenger Car Unit (PCU) equivalence coefficients from the Transport Research Laboratory (TRL Overseas Road Note 13, 1996); and standard traffic signal clearance formulas and lost-time constants established by the Federal Highway Administration (FHWA Traffic Signal Timing Manual, Koonce et al., 2008).")

add_heading_2(doc, "3.8  Methods of Data Collection")
add_para(doc, "Video streams were acquired using a smartphone optical sensor deployed as a non-intrusive edge camera. Data transport was achieved through three supported network protocol pipelines: an HTTP Motion-JPEG (MJPEG) pipeline streaming consecutive JPEG frames at 1080p over 802.11ac wireless; an RTSP (Real-Time Streaming Protocol) pipeline delivering low-latency H.264 video; and a direct USB virtual video capture pipeline eliminating wireless packet jitter.")
add_para(doc, "To resolve internal client-side buffering issues common in standard OpenCV video capture—which introduce 3 to 10 seconds of latent delay on network streams—a dedicated asynchronous multithreaded reader (LiveStreamCapture) was engineered. The frame grabber continuously executes a background thread that flushes decoded frames from the hardware ring buffer, ensuring that the main inference thread always retrieves only the freshest frame (latency < 35 ms).")

add_heading_2(doc, "3.9  Research Instruments")
add_para(doc, "The hardware and software instruments employed in the study are specified below:")

# Table 3.2 Hardware Specifications
table3_2 = doc.add_table(rows=1, cols=3)
table3_2.alignment = WD_TABLE_ALIGNMENT.CENTER
t32_hdrs = table3_2.rows[0].cells
t32_hdrs[0].text = "Subsystem Component"
t32_hdrs[1].text = "Technical Specification"
t32_hdrs[2].text = "Operational Role"
for c in t32_hdrs:
    for p in c.paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            format_run(r, r.text, size_pt=9.5, bold=True)

hw_specs = [
    ("Mobile Optical Sensor", "Android Smartphone, 48 MP primary sensor, f/1.8 aperture, 1080p @ 30 fps, 802.11ac Wi-Fi", "Primary optical field camera overlooking intersection"),
    ("Edge Compute Host", "Standard x86_64 PC, Intel Core multi-core CPU @ 2.60 GHz base, 16 GB DDR4 RAM", "Central inference processing, queue estimation & FSM"),
    ("Local Network Router", "Dual-Band (2.4 GHz / 5.0 GHz) 802.11ac Wireless Gateway, 1200 Mbps", "Dedicated local wireless LAN connecting camera to host"),
    ("Mounting Hardware", "Heavy-duty 2.1 m tripod with 360° fluid damping head", "Optical stability during multi-viewpoint field recording"),
]

for hw in hw_specs:
    rc = table3_2.add_row().cells
    for i, val in enumerate(hw):
        rc[i].text = val
        for p in rc[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                format_run(r, r.text, size_pt=8.5)

add_para(doc, "", space_after=8)

# Table 3.3 Software Specifications
table3_3 = doc.add_table(rows=1, cols=3)
table3_3.alignment = WD_TABLE_ALIGNMENT.CENTER
t33_hdrs = table3_3.rows[0].cells
t33_hdrs[0].text = "Software Library / Tool"
t33_hdrs[1].text = "Version"
t33_hdrs[2].text = "Functional Responsibility"
for c in t33_hdrs:
    for p in c.paragraphs:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            format_run(r, r.text, size_pt=9.5, bold=True)

sw_specs = [
    ("Python Runtime", "3.13.0 (64-bit)", "Core program execution and multithreaded runtime environment"),
    ("Ultralytics YOLO", "8.3.0+", "Deep-learning object detection pipeline and model weights management"),
    ("PyTorch (torch)", "2.6.0+cpu", "CPU-optimized tensor execution backend and forward-pass engine"),
    ("OpenCV (cv2)", "4.10.0", "Image manipulation, frame decoding, polygon geometry tests, HUD drawing"),
    ("NumPy", "2.1.0+", "Vectorized 2D array operations, coordinate normalization, bounding-box math"),
    ("IP Webcam Engine", "1.15.0+", "Mobile RTSP/MJPEG server software broadcasting raw camera frames"),
    ("Matplotlib", "3.10.0", "Generation of architectural schematics, DFDs, and analytical plots"),
]

for sw in sw_specs:
    rc = table3_3.add_row().cells
    for i, val in enumerate(sw):
        rc[i].text = val
        for p in rc[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                format_run(r, r.text, size_pt=8.5)

add_para(doc, "", space_after=8)

add_heading_2(doc, "3.10  Validity and Reliability")
add_para(doc, "To establish internal validity, approach Regions of Interest (ROIs) are stored as dimensionless normalized coordinate pairs (x_norm, y_norm) ∈ [0.0, 1.0] x [0.0, 1.0]. This guarantees that spatial queue definitions remain invariant regardless of whether input video streams change dynamically between 720p, 1080p, or 4K resolutions. Furthermore, vehicle zone membership is evaluated strictly at the base-center contact point (the midpoint of the bottom bounding box line: C_base = ((x1 + x2)/2, y2)), eliminating perspective distortion errors where tall commercial vehicles project their visual centers into adjacent traffic lanes.")
add_para(doc, "External validity is achieved by mapping the four COCO vehicle classes to the local Lagos vehicle fleet: COCO Class 2 (car) represents private sedans, station wagons, and SUVs; Class 3 (motorcycle) represents commercial okadas; Class 5 (bus) represents commercial danfo minibuses and institutional shuttles; and Class 7 (truck) represents delivery trucks and refuse vehicles. Commercial tricycles (keke), which have geometric profiles intermediate between motorcycles and compact cars, are consistently detected under Class 2 or Class 3 depending on perspective.")
add_para(doc, "Reliability and repeatability are enforced by utilizing the replay simulation engine (simulate_viewpoints.py), which feeds identical recorded video frames to both the adaptive controller and the baseline fixed-time controller, ensuring strictly controlled, repeatable comparative evaluations.")

add_heading_2(doc, "3.11  Analysis of the Existing System")
add_para(doc, "Currently, the intersection at YABATECH Front Gate lacks any automated traffic signal installation. Traffic movement is governed exclusively by informal self-regulation (driver negotiation, vehicle size dominance, aggressive horn use) or intermittent manual traffic warden direction by LASTMA or police officers. Manual control suffers from line-of-sight restrictions (wardens cannot see queue buildup extending 150 meters upstream), reaction lag, asymmetric bias, and physical fatigue under tropical heat or heavy rainfall.")
add_para(doc, "Under a hypothetical fixed-time signal installation, signal splits would follow rigid durations (e.g., 30 s green per phase). Webster's classical delay formula demonstrates that when traffic arrivals are asymmetric—such as during morning peaks where Hussey Road experiences heavy inbound flow while Alakija Street and the Campus Gate have minimal traffic—fixed-time signals waste substantial green time on empty approaches while queues on the loaded corridor grow exponentially. This mathematical mismatch confirms the necessity of demand-responsive adaptive control.")

add_heading_2(doc, "3.12  Design of the Proposed Solution")
add_para(doc, "The proposed solution is structured into four distinct, loosely coupled architectural layers: Layer 1: Data Acquisition and Threaded Buffering; Layer 2: Computer Vision and Perception Engine; Layer 3: Adaptive Traffic Signal Controller; and Layer 4: Visualization, Telemetry, and Logging.")

# Insert Figure 3.1
fig_3_1_path = fig_dir / "Figure_3_1_System_Architecture.png"
add_figure_image(doc, fig_3_1_path, "Figure 3.1: High-Level System Architecture of the Adaptive Traffic Signal Control System")

add_para(doc, "Figure 3.1 outlines the multi-tiered architecture. Layer 1 captures the camera stream and flushes buffers. Layer 2 runs the YOLO11n object detector on the CPU, extracts bottom-center vehicle centroids, and evaluates polygon inclusion using cv2.pointPolygonTest. Layer 3 maintains the signal controller finite-state machine (GREEN -> YELLOW -> ALL-RED), calculates dynamic green durations, and monitors gap-out early termination. Layer 4 renders high-visibility signal pods, badges, and countdown timers on the video output while logging diagnostic telemetry to CSV.")

# Insert Figure 3.2
fig_3_2_path = fig_dir / "Figure_3_2_Context_Diagram.png"
add_figure_image(doc, fig_3_2_path, "Figure 3.2: Level 0 Context Diagram of the Adaptive Traffic Signal Control System")

add_para(doc, "Figure 3.2 illustrates the system context diagram (DFD Level 0). External entities comprise the Smartphone Camera (supplying live video streams), Approaching Traffic at the YABATECH intersection (optical vehicle movements), the Signal Hardware / Virtual HUD Display (receiving signal phase actuation commands), and the Traffic Engineer / LASTMA Analyst (configuring ROI polygons and receiving real-time diagnostic reports).")

# Insert Figure 3.3
fig_3_3_path = fig_dir / "Figure_3_3_Data_Flow_Diagram.png"
add_figure_image(doc, fig_3_3_path, "Figure 3.3: Level 1 Data Flow Diagram (DFD) of the Adaptive Traffic Signal Control System")

add_para(doc, "Figure 3.3 details the Level 1 Data Flow Diagram. The architecture decomposes into five core processes: Process 1.0 (Capture & Buffer Video Frames), Process 2.0 (Detect & Classify Vehicles via YOLO), Process 3.0 (Estimate Approach Queues via Polygonal ROIs), Process 4.0 (Compute Dynamic Green Time & Evaluate State Machine), and Process 5.0 (Render HUD & Export Telemetry). Four internal data stores (D1: Approach ROI Polygon Store, D2: Real-Time Queue Store, D3: Controller Timing Parameters, and D4: Simulation Telemetry Log) maintain state persistence.")

add_heading_3(doc, "Mathematical Formulation of Control Logic")
add_para(doc, "The adaptive controller logic is governed by four primary mathematical formulations:")
add_para(doc, "1. Ground Contact Centroid: For bounding box coordinates (x1, y1, x2, y2), the ground contact point C_i is calculated as:")
p = add_para(doc, "C_x = (x1 + x2) / 2,    C_y = y2", align=WD_ALIGN_PARAGRAPH.CENTER)
r = p.runs[0]; format_run(r, p.text, bold=True)

add_para(doc, "2. Queue Aggregation: The queue count Q_k for approach polygon P_k is computed via the point-in-polygon winding number test:")
p = add_para(doc, "Q_k = SUM [ I( cv2.pointPolygonTest(P_k, C_i, False) >= 0 ) ]", align=WD_ALIGN_PARAGRAPH.CENTER)
r = p.runs[0]; format_run(r, p.text, bold=True)

add_para(doc, "3. Dynamic Green Allocation: The green time T_green allocated to approach k is dynamically calculated based on queue size:")
p = add_para(doc, "T_green(k) = clip( T_min + (Q_k * T_car),  T_min,  T_max )", align=WD_ALIGN_PARAGRAPH.CENTER)
r = p.runs[0]; format_run(r, p.text, bold=True)
add_para(doc, "where T_min = 8.0 s, T_max = 35.0 s, and T_car = 2.0 s/vehicle.")

add_para(doc, "4. Gap-Out Early Termination Logic: The active green phase terminates early to yellow if:")
p = add_para(doc, "( t_elapsed >= T_min )  AND  ( Q_active == 0 )  AND  ( any(Q_other > 0) )", align=WD_ALIGN_PARAGRAPH.CENTER)
r = p.runs[0]; format_run(r, p.text, bold=True)
add_para(doc, "All phase transitions enforce a fixed yellow interval (T_yellow = 3.0 s) and an all-red clearance interval (T_all_red = 2.0 s).")

add_heading_2(doc, "3.13  Development/Implementation Methodology")
add_para(doc, "The software was built using Agile Prototyping across four iterative sprints within the Design Science Research framework: Sprint 1 implemented the multithreaded frame capture engine; Sprint 2 integrated YOLO11n and the interactive polygonal ROI calibration interface; Sprint 3 implemented the finite-state machine adaptive signal controller with dynamic green scaling and gap-out logic; and Sprint 4 developed the high-visibility traffic HUD overlay, the offline multi-viewpoint replay simulator, and CSV telemetry logging.")

add_heading_2(doc, "3.14  Hardware Requirements")
add_para(doc, "The system operates on standard, cost-effective hardware. Recommended host workstation specifications include an Intel Core i5/i7 (or equivalent multi-core CPU @ 2.60 GHz or higher), 16 GB DDR4 RAM, 50 GB SSD storage, and an 802.11ac wireless interface. The mobile optical sensor requires a standard Android smartphone with at least a 1080p @ 30 fps camera and Wi-Fi / USB tethering capabilities. No external CUDA GPU is required, ensuring that the system can be deployed on modest edge computing setups.")

add_heading_2(doc, "3.15  Software Requirements")
add_para(doc, "The software stack executes under 64-bit Windows 10/11 or Ubuntu Linux 20.04/22.04 LTS. The primary runtime environment is Python 3.13, utilizing Ultralytics YOLO (8.3.0+) with PyTorch CPU backend, OpenCV-Python (4.10.0+), NumPy (2.1.0+), and Matplotlib (3.10.0+). All dependencies are managed in an isolated virtual environment (`venv`).")

add_heading_2(doc, "3.16  Proposed Implementation Procedure")
add_para(doc, "The end-to-end execution procedure follows a structured algorithm:")
proc_steps = [
    "Step 1: System Startup and Ingestion Handshake — Initialize LiveStreamCapture worker thread on the target RTSP/HTTP camera stream URI.",
    "Step 2: Approach Zone Configuration Loading — Load normalized ROI polygon coordinates from outputs/approach_zones.json. If absent, launch interactive setup mode allowing the user to click 4 corner vertices per approach on the initial frame.",
    "Step 3: Neural Model Initialization — Load YOLO11n weights into CPU tensor memory with confidence threshold tau = 0.25.",
    "Step 4: Real-Time Frame Processing Loop — Ingest decoupled latest frame; run YOLO forward pass; filter vehicle classes; calculate base-center ground contact points ((x1+x2)/2, y2).",
    "Step 5: Spatial Polygon Containment Evaluation — Execute pointPolygonTest for each detected vehicle across all defined approach polygons; update instantaneous queue counts Q_k.",
    "Step 6: Signal Controller State Machine Evaluation — Evaluate elapsed time in current state: if GREEN, check for gap-out (queue cleared) or timer expiration to trigger YELLOW; if YELLOW, transition to ALL-RED after 3.0 s; if ALL-RED, select next approach with highest queue, calculate T_green, and transition to GREEN after 2.0 s.",
    "Step 7: Visual Overlay and Telemetry Export — Render 3-lamp signal pods, status badges, and countdown timers via draw_high_visibility_hud(); write frame records to CSV; present annotated display frame.",
    "Step 8: Stream Termination and Handle Cleanup — On keyboard break, terminate capture worker thread, release window handles, and close CSV logging files."
]
for pstep in proc_steps:
    add_para(doc, pstep)

add_heading_2(doc, "3.17  Method of Data Analysis")
add_para(doc, "Quantitative comparative performance analysis evaluates five primary metrics: Mean Queue Length (Q_mean), Maximum Queue Spike (Q_max), Green Time Allocation Ratio (rho_k), Phase Switching Frequency (N_cycles), and Computational Throughput (FPS).")
add_para(doc, "Statistical hypothesis testing evaluates whether the adaptive controller allocates significantly more green time to the loaded approach compared to a fixed-time controller. The test is conducted using a two-sample paired Student's t-test (and confirmed via the non-parametric Wilcoxon signed-rank test for non-normal distributions) across paired 30-second observation intervals at a significance threshold of alpha = 0.05. A calculated p-value < 0.05 rejects the null hypothesis H0 in favor of H1, establishing statistically significant superiority.")

add_heading_2(doc, "3.18  Proposed Testing and Validation")
add_para(doc, "System verification is organized across four distinct validation tiers:")
add_para(doc, "1. Tier 1: Unit and Component Testing — Verifying non-blocking frame grabber operation (latency < 35 ms), polygon containment arithmetic, and controller timing bounds [T_min, T_max].")
add_para(doc, "2. Tier 2: Computer Vision Perception Validation — Measuring vehicle detection precision (>= 0.85) and recall (>= 0.80) against 100 manually annotated ground-truth intersection frames across diverse lighting.")
add_para(doc, "3. Tier 3: Multi-Viewpoint Simulation Replay Testing — Running a 6-minute continuous benchmark test on main_intersection.mp4 (2,371 frames), evaluating 20 full adaptive phase switches, gap-out responsiveness, and queue dissipation.")
add_para(doc, "4. Tier 4: Stress and Edge-Case Testing — Validating system stability under sudden camera stream disconnection, zero-traffic conditions (confirming round-robin fallback), and severe asymmetric queue saturation.")

doc.save(target_docx)
print(f"Complete document successfully compiled to: {target_docx}")
