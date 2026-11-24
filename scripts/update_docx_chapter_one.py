import copy
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

src_path = r'C:\Users\User\.gemini\antigravity\brain\8ee10a4d-a16c-4b92-9f05-58bda56a318e\.user_uploaded\media_1795508022427_2c2764a5.docx'
out_path = r'c:\Users\User\yabatech-traffic-poc\outputs\YABATECH_Adaptive_Traffic_PoC_Chapter_One.docx'

doc = Document(src_path)

# Helper function to set run styling cleanly
def set_run(run, text, font_name="Times New Roman", size_pt=12, bold=None, italic=None):
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic

# 1. Update Title Page (Paragraph 8)
p8 = doc.paragraphs[8]
p8.text = ""
r8 = p8.add_run()
set_run(r8, "ADAPTIVE TRAFFIC SIGNAL CONTROL USING REAL-TIME COMPUTER VISION AND VEHICLE QUEUE ESTIMATION: A PROOF-OF-CONCEPT FOR THE YABATECH FRONT GATE INTERSECTION", size_pt=15, bold=True)
p8.alignment = WD_ALIGN_PARAGRAPH.CENTER

# 2. Update Summary of Proposed Study (Paragraphs 17, 18, 19)
p17 = doc.paragraphs[17]
p17.text = ""
r17 = p17.add_run()
set_run(r17, "This study develops an Adaptive Traffic Signal Control system that uses a live camera feed from a smartphone, a deep-learning object detection model (YOLO), and region-of-interest-based vehicle queue estimation to decide, in real time, how much green time each approach of a junction should receive. The system is built as a proof-of-concept and tested at the intersection in front of the Yaba College of Technology (YABATECH) Front Gate on Hussey Road, Yaba, Lagos State.")
p17.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

p18 = doc.paragraphs[18]
p18.text = ""
r18 = p18.add_run()
set_run(r18, "The aim is to design, implement, and evaluate this computer-vision-based adaptive signal controller for the selected intersection. The study follows the Design Science Research approach. Information on how traffic is currently handled at the junction is gathered through on-site observation and video recording from multiple viewpoints, and the system is built iteratively in Python using the Ultralytics YOLO framework, OpenCV, and NumPy. Performance is evaluated by running the adaptive controller on recorded intersection video and comparing the resulting signal phase distributions with what a fixed-time controller would have produced under the same traffic conditions.")
p18.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

p19 = doc.paragraphs[19]
p19.text = ""
r19 = p19.add_run()
set_run(r19, "The system is expected to demonstrate that a low-cost, camera-based adaptive signal controller can respond to real traffic conditions at a Lagos junction without requiring embedded road sensors, and to serve as a working prototype that can be extended to other locations.")
p19.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 3. Update List of Figures (Paragraphs 71 and 72)
p71 = doc.paragraphs[71]
p71.text = ""
r71_1 = p71.add_run()
set_run(r71_1, "Figure 3.2  ", bold=True)
r71_2 = p71.add_run()
set_run(r71_2, "Level 0 Context Diagram of the Adaptive Traffic Signal Control System")

p72 = doc.paragraphs[72]
p72.text = ""
r72_1 = p72.add_run()
set_run(r72_1, "Figure 3.3  ", bold=True)
r72_2 = p72.add_run()
set_run(r72_2, "Level 1 Data Flow Diagram of the Adaptive Traffic Signal Control System")

# 4. Update List of Abbreviations
abbreviations = [
    ("CNN", "Convolutional Neural Network"),
    ("DFD", "Data Flow Diagram"),
    ("DSR", "Design Science Research"),
    ("FPS", "Frames Per Second"),
    ("HND", "Higher National Diploma"),
    ("ITS", "Intelligent Transport Systems"),
    ("LASTMA", "Lagos State Traffic Management Authority"),
    ("OpenCV", "Open Source Computer Vision Library"),
    ("ROI", "Region of Interest"),
    ("YOLO", "You Only Look Once"),
]

# Currently p75 to p81 are the 7 abbreviations. We can clear them, refill them, and insert extra ones right before p82.
# Let's inspect p82: it's an empty line before p83 ("CHAPTER ONE").
# First, update the existing 7 paragraphs p75-p81:
for idx in range(7):
    p = doc.paragraphs[75 + idx]
    p.text = ""
    abbr, meaning = abbreviations[idx]
    r1 = p.add_run()
    set_run(r1, abbr, bold=True)
    r2 = p.add_run()
    set_run(r2, f"\t{meaning}")

# For remaining abbreviations (idx 7, 8, 9), insert before paragraph 82
# In python-docx, p.insert_paragraph_before() inserts before paragraph.
p_target = doc.paragraphs[82]
for idx in range(7, len(abbreviations)):
    p = p_target.insert_paragraph_before()
    p.style = doc.styles['Normal']
    abbr, meaning = abbreviations[idx]
    r1 = p.add_run()
    set_run(r1, abbr, bold=True)
    r2 = p.add_run()
    set_run(r2, f"\t{meaning}")

# 5. Now update Chapter One paragraphs
# Let's find CHAPTER ONE paragraph index dynamically to be safe:
ch1_idx = None
for i, p in enumerate(doc.paragraphs):
    if p.text.strip() == "CHAPTER ONE":
        ch1_idx = i
        break

print(f"CHAPTER ONE found at index: {ch1_idx}")

# The paragraphs following CHAPTER ONE:
# ch1_idx + 1: INTRODUCTION (Heading)
# ch1_idx + 2: 1.1  Background to the Study
# ch1_idx + 3: Background para 1 (United Nations...)
# ch1_idx + 4: Background para 2 (Traffic signals...)
# ch1_idx + 5: Background para 3 (Lagos...)
# ch1_idx + 6: Background para 4 (Lagos State Govt...)
# ch1_idx + 7: Background para 5 (ITS / Computer vision...)
# ch1_idx + 8: Background para 6 (This study takes that approach / Despite...)

# Let's update 1.1 paragraphs:
p_bg2 = doc.paragraphs[ch1_idx + 4]
p_bg2.text = ""
r_bg2 = p_bg2.add_run()
set_run(r_bg2, "Traffic signals are one of the main tools cities use to manage this pressure. The traditional type works on fixed timing: each direction gets a set number of seconds of green light, whatever the traffic looks like at that moment. That works reasonably well when traffic is steady, but it wastes time when one road is packed and another is nearly empty. To deal with this, many cities have moved to adaptive signal control, where sensors detect the vehicles and the timing is adjusted as conditions change. Field studies reviewed by the United States Department of Transportation (2015) report travel time reductions of up to about 29 per cent after adaptive systems were installed, although the results differ from one location to another.")
p_bg2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

p_bg5 = doc.paragraphs[ch1_idx + 7]
p_bg5.text = ""
r_bg5 = p_bg5.add_run()
set_run(r_bg5, "Recent advances in computer vision and deep learning have opened a new and more affordable path. Object detection models such as YOLO (You Only Look Once), introduced by Redmon, Divvala, Girshick and Farhadi (2016) and since refined through several generations, can identify and count vehicles in a video frame in real time, even on modest hardware. When this capability is combined with a live camera feed — which can now come from an ordinary smartphone — it becomes possible to estimate the number of vehicles queued on each approach of a junction without installing any embedded road sensors. The queue estimates can then drive an adaptive signal timing algorithm that gives more green time to the busier approach and less to the quieter one.")
p_bg5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

p_bg6 = doc.paragraphs[ch1_idx + 8]
p_bg6.text = ""
r_bg6 = p_bg6.add_run()
set_run(r_bg6, "This study takes that approach. It develops a proof-of-concept adaptive traffic signal controller that uses a live smartphone camera stream, the YOLO object detection model, and region-of-interest-based vehicle queue estimation to control signal phases at a real Lagos intersection: the junction in front of the Yaba College of Technology (YABATECH) Front Gate on Hussey Road, Yaba. The intersection is a multi-leg junction where Hussey Road meets Alakija Street and the YABATECH campus entrance, handling a mix of cars, buses, tricycles (keke) and motorcycles at all hours of the day. Despite the importance of this issue, several challenges still exist, which necessitate this study.")
p_bg6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.2 Statement of the Problem
# Find 1.2 heading
p12_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.2"):
        p12_idx = i
        break

doc.paragraphs[p12_idx + 1].text = ""
r = doc.paragraphs[p12_idx + 1].add_run()
set_run(r, "The main problem this study addresses is that traffic signals at many Lagos junctions, including the YABATECH Front Gate intersection on Hussey Road, cannot respond to the amount of traffic actually on the road. From what can be observed at the study junction, the signals follow fixed timings when they are operational, and at other times traffic officers or informal self-regulation by drivers is the only form of control. The result is long queues on busy approaches while green time is wasted on roads with few vehicles.")
doc.paragraphs[p12_idx + 1].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.paragraphs[p12_idx + 2].text = ""
r = doc.paragraphs[p12_idx + 2].add_run()
set_run(r, "Several groups are affected. Commuters, including the thousands of students and staff who pass through the YABATECH gate daily, lose time and spend more on fuel, with the Danne Institute for Research (2021) putting the average time Lagosians spend in traffic at 2.21 hours daily. Traffic officers work without data and can only react after a jam has formed. Government agencies have no reliable, continuous record of traffic volumes at the junction, so planning decisions rest on limited information.")
doc.paragraphs[p12_idx + 2].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.paragraphs[p12_idx + 3].text = ""
r = doc.paragraphs[p12_idx + 3].add_run()
set_run(r, "Conventional adaptive traffic systems rely on embedded road sensors — inductive loops, magnetometers or radar units — that are expensive to install and maintain, particularly in a developing-country setting where road surfaces are frequently disrupted. This cost barrier has prevented the adoption of adaptive signal control at many Lagos junctions.")
doc.paragraphs[p12_idx + 3].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.paragraphs[p12_idx + 4].text = ""
r = doc.paragraphs[p12_idx + 4].add_run()
set_run(r, "This study therefore addresses the need for a low-cost, vision-based adaptive signal control system that uses a smartphone camera and deep-learning vehicle detection to adjust signal timing in response to real traffic conditions, without requiring embedded road sensors.")
doc.paragraphs[p12_idx + 4].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.3 Aim of the Study
p13_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.3"):
        p13_idx = i
        break

doc.paragraphs[p13_idx + 1].text = ""
r = doc.paragraphs[p13_idx + 1].add_run()
set_run(r, "The aim of this study is to design, implement, and evaluate a proof-of-concept adaptive traffic signal control system that uses real-time computer vision and vehicle queue estimation from a live smartphone camera feed to adjust signal timing at the YABATECH Front Gate intersection on Hussey Road, Yaba, Lagos State.")
doc.paragraphs[p13_idx + 1].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.4 Objectives of the Study
p14_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.4"):
        p14_idx = i
        break

objectives = [
    "Examine how traffic is currently managed at the YABATECH Front Gate intersection and the problems faced by road users and any traffic officers deployed there.",
    "Design a system architecture that captures a live video stream from a smartphone camera, detects and counts vehicles using the YOLO object detection model, and estimates the queue length on each approach of the junction using region-of-interest polygons.",
    "Develop an adaptive signal timing algorithm that adjusts the green time of each approach based on the number of vehicles currently queued, with appropriate safety intervals (yellow and all-red clearance phases).",
    "Implement the system as a working proof-of-concept in Python, using OpenCV for video capture, the Ultralytics YOLO framework for vehicle detection, and a state-machine signal controller.",
    "Evaluate the system by running it on recorded intersection video from multiple viewpoints and analysing the resulting signal phase distributions, queue response behaviour, and processing throughput."
]

for k, obj in enumerate(objectives):
    p = doc.paragraphs[p14_idx + 2 + k]
    p.text = ""
    r = p.add_run()
    set_run(r, obj)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.5 Research Questions
p15_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.5"):
        p15_idx = i
        break

questions = [
    "How is traffic currently managed at the YABATECH Front Gate intersection, and what are the main problems observed?",
    "What system architecture can capture a live smartphone camera feed, detect vehicles using deep learning, and estimate queue lengths on each approach?",
    "How can signal timing be adjusted automatically based on the number of vehicles queued on each approach, while maintaining safe clearance intervals?",
    "Can a proof-of-concept implementation running on consumer-grade hardware process a live video stream fast enough to make timely signal decisions?",
    "To what extent does the adaptive timing respond appropriately to changing traffic conditions compared with a fixed-time signal plan?"
]

for k, q in enumerate(questions):
    p = doc.paragraphs[p15_idx + 2 + k]
    p.text = ""
    r = p.add_run()
    set_run(r, q)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.6 Research Hypotheses
p16_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.6"):
        p16_idx = i
        break

doc.paragraphs[p16_idx + 1].text = ""
r = doc.paragraphs[p16_idx + 1].add_run()
set_run(r, "The evaluation stage compares the behaviour of the adaptive controller with that of a fixed-time plan under the same traffic conditions, so one pair of hypotheses is stated.")
doc.paragraphs[p16_idx + 1].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.paragraphs[p16_idx + 2].text = ""
r = doc.paragraphs[p16_idx + 2].add_run()
set_run(r, "H₀: There is no significant difference in signal responsiveness (measured by the proportion of green time allocated to the busier approach) between fixed-time signal control and the proposed vision-based adaptive control.")
doc.paragraphs[p16_idx + 2].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.paragraphs[p16_idx + 3].text = ""
r = doc.paragraphs[p16_idx + 3].add_run()
set_run(r, "H₁: The proposed vision-based adaptive control allocates a significantly higher proportion of green time to the busier approach than fixed-time signal control does.")
doc.paragraphs[p16_idx + 3].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.7 Significance of the Study
p17_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.7"):
        p17_idx = i
        break

sig_paras = [
    "Traffic management agencies, including LASTMA, stand to gain the most. The study demonstrates that adaptive signal control can be achieved with an ordinary smartphone camera and open-source software, without the capital cost of embedded road sensors. If the approach proves effective, it offers a path to upgrading signal control at junctions across Lagos at a fraction of the cost of conventional sensor-based systems.",
    "Road users — commuters, students, staff, and commercial vehicle operators who pass through the YABATECH Front Gate intersection daily — would benefit from signal timing that responds to actual demand. Even modest improvements in green-time allocation at a busy junction can reduce idle time and fuel consumption.",
    "Planners and policymakers would gain evidence on whether smartphone-camera-based vehicle detection is accurate and fast enough for real-time signal control in a Lagos traffic environment, which includes a mix of cars, buses, tricycles and motorcycles, often in poor road-surface and lighting conditions.",
    "For the academic community, the study offers a documented, reproducible example of combining deep-learning object detection (YOLO) with an adaptive signal timing algorithm in a proof-of-concept system. The code, data and methodology are available for other students and researchers to adapt, test and improve upon."
]

for k, sp in enumerate(sig_paras):
    p = doc.paragraphs[p17_idx + 1 + k]
    p.text = ""
    r = p.add_run()
    set_run(r, sp)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.8 Scope of the Study
p18_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.8"):
        p18_idx = i
        break

scope_paras = [
    "In terms of subject, the study covers the design and implementation of a proof-of-concept adaptive traffic signal control system. This includes capturing a live video stream from a smartphone camera, detecting and counting vehicles using the YOLO object detection model, estimating queue lengths on each approach using region-of-interest polygons, and running an adaptive signal timing algorithm with green, yellow and all-red phases. It does not cover the physical installation of traffic signal hardware, number-plate recognition, speed enforcement, fines, or any other form of traffic law enforcement.",
    "Geographically, the study is limited to the intersection in front of the YABATECH Front Gate on Hussey Road, Yaba, Lagos State. This is a multi-leg junction where Hussey Road intersects with Alakija Street and the campus entrance. The road extends westward past the WAEC Building and the 68 Nigerian Army Reference Hospital (Military Hospital, Yaba) toward the Federal Science and Technical College (FSTC) Yaba, and eastward toward Higher College Road and the junction at the Jibowu Pedestrian Bridge. The design can be extended to other junctions, but only this one is tested in this study.",
    "Functionally, the system processes a single camera viewpoint at a time and controls signal phases for the approaches visible from that viewpoint. It does not implement a multi-camera fusion system covering all approaches simultaneously, although the architecture is designed to support such extension. In terms of hardware, the proof-of-concept runs on a standard laptop computer without a dedicated GPU, using CPU-based inference. In terms of time, the study runs from requirement gathering through design, implementation and testing, within the period given for the project."
]

for k, sc in enumerate(scope_paras):
    p = doc.paragraphs[p18_idx + 1 + k]
    p.text = ""
    r = p.add_run()
    set_run(r, sc)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.9 Overview of the Research Methodology
p19_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.9"):
        p19_idx = i
        break

method_paras = [
    "The study follows the Design Science Research (DSR) approach, which suits projects whose main output is a working system or artefact (Hevner, March, Park and Ram, 2004). Observation at the selected junction, including video recording from multiple viewpoints, provides the primary data on traffic flow patterns, vehicle types and queue behaviour. Secondary data comes from journal articles, government reports and earlier studies on adaptive traffic control and computer vision for vehicle detection.",
    "The system is built iteratively in Python. The Ultralytics YOLO framework is used for vehicle detection, OpenCV handles video capture and display, and NumPy supports the geometric computations for region-of-interest queue estimation. The adaptive signal timing algorithm is implemented as a finite-state machine with configurable parameters for minimum and maximum green time, time per vehicle, yellow duration and all-red clearance. An interactive setup mode allows the user to define approach zone polygons for any camera viewpoint by clicking on the video frame.",
    "For evaluation, the system is run on recorded video of the intersection captured from several viewpoints. The metrics collected include the number of vehicles detected per frame, the queue count on each approach at each phase transition, the green time allocated to each approach, the number of phase transitions, and the processing speed in frames per second. These are compared with the behaviour that a fixed-time controller would produce under the same traffic input. The full method is explained in Chapter Three."
]

# Note: In original, there were 2 paragraphs for 1.9. We have 3 paragraphs.
# Let's insert a paragraph before 1.10 if needed.
p110_idx = None
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.10"):
        p110_idx = i
        break

# Number of paragraphs between p19_idx and p110_idx:
existing_between = p110_idx - p19_idx - 1
print(f"Existing paragraphs in 1.9: {existing_between}")

doc.paragraphs[p19_idx + 1].text = ""
r = doc.paragraphs[p19_idx + 1].add_run()
set_run(r, method_paras[0])
doc.paragraphs[p19_idx + 1].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.paragraphs[p19_idx + 2].text = ""
r = doc.paragraphs[p19_idx + 2].add_run()
set_run(r, method_paras[1])
doc.paragraphs[p19_idx + 2].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# If there was only 2 paragraphs, insert the 3rd one before 1.10
if existing_between == 2:
    p_third = doc.paragraphs[p110_idx].insert_paragraph_before()
    p_third.style = doc.styles['Normal']
    r = p_third.add_run()
    set_run(r, method_paras[2])
    p_third.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
else:
    doc.paragraphs[p19_idx + 3].text = ""
    r = doc.paragraphs[p19_idx + 3].add_run()
    set_run(r, method_paras[2])
    doc.paragraphs[p19_idx + 3].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# 1.10 Definition of Terms
# Re-locate 1.10
for i in range(ch1_idx, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip().startswith("1.10"):
        p110_idx = i
        break

definitions = [
    ("Adaptive Traffic Signal Control:  ", "In this study, a system that adjusts the green time given to each approach of a junction based on the number of vehicles currently detected, instead of following a fixed schedule."),
    ("Computer Vision:  ", "The use of algorithms to extract meaningful information from images or video, in this case to detect and count vehicles."),
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

# There were 9 definitions originally (paragraphs p110_idx + 1 to p110_idx + 9).
# We have 12 definitions.
for k in range(min(9, len(definitions))):
    p = doc.paragraphs[p110_idx + 1 + k]
    p.text = ""
    term, explanation = definitions[k]
    r1 = p.add_run()
    set_run(r1, term, bold=True)
    r2 = p.add_run()
    set_run(r2, explanation)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# For definitions beyond 9 (k=9, 10, 11), append or insert
for k in range(9, len(definitions)):
    p = doc.add_paragraph()
    p.style = doc.styles['Normal']
    term, explanation = definitions[k]
    r1 = p.add_run()
    set_run(r1, term, bold=True)
    r2 = p.add_run()
    set_run(r2, explanation)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.save(out_path)
print(f"Successfully saved updated document to: {out_path}")
