# OCR Architectural Comparison: EasyOCR vs. Donut

When extracting text from clinical notes and prescriptions, you have two primary architectural paradigms to choose from: the **Classical CNN-RNN Pipeline** (EasyOCR) and the **Modern Vision-Language Transformer Pipeline** (Donut).

## 1. EasyOCR (The Classical Pipeline)

`EasyOCR` is a highly popular, pure Python-friendly library. It operates using a multi-stage pipeline:

1.  **Detection (CRAFT Algorithm):** First, a Convolutional Neural Network (CNN) scans the image specifically looking for regions that look like text. It draws bounding boxes around every word or line it finds.
2.  **Recognition (CRNN):** Next, the image inside each bounding box is cropped out and passed to a Convolutional Recurrent Neural Network (CRNN). The CNN extracts visual features from the cropped text, and an RNN (like an LSTM) decodes those visual features into a sequence of characters.

**Pros for MedVision:**
*   **Fast and Lightweight:** Extremely fast on CPU/GPU.
*   **Plug-and-Play:** Works immediately on raw text without needing specific layouts.
*   **High Accuracy on Standard Text:** Very reliable for standard printed text in lab reports.

**Cons for MedVision:**
*   **Loses Context:** Because it crops out individual words, it doesn't inherently understand that "Dosage" is connected to "500mg" if they are far apart.
*   **Handwriting Struggles:** While decent, doctors' cursive handwriting can sometimes confuse the bounding box detector.

---

## 2. Donut (The Modern Transformer Pipeline)

`Donut` (Document Understanding Transformer) represents a massive shift in how we handle document AI. It completely eliminates the bounding box detection step.

1.  **Vision Encoder (Swin Transformer):** The entire document image is fed into a Vision Transformer. Instead of looking for bounding boxes, the transformer breaks the image into a grid of patches and learns the visual "embeddings" of the entire document's structure simultaneously.
2.  **Language Decoder (BART):** A language transformer takes those visual embeddings and generates a structured JSON output directly (e.g., `{"medicine": "Amoxicillin", "dosage": "500mg"}`).

**Pros for MedVision:**
*   **Understands Layouts:** It understands the spatial relationship between words. It knows *where* a dosage usually appears relative to a medicine name.
*   **End-to-End Structured Data:** It outputs structured JSON instead of a raw string of text.
*   **No Bounding Boxes:** Extremely robust against messy handwriting or slightly misaligned scans because it doesn't rely on drawing perfect boxes first.

**Cons for MedVision:**
*   **Resource Intensive:** Transformers are massive. They require significantly more VRAM/GPU power to run efficiently.
*   **Slower Inference:** Slower than EasyOCR, especially on CPUs.

## Our MedVision Strategy

As requested, we will start by implementing our OCR preprocessing and extraction pipelines using **EasyOCR** to maintain our fast inference speeds and low resource overhead. However, we will architect our `ocr_service.py` with an abstraction layer (a Strategy Pattern) so that we can easily swap in the Donut Transformer later if we find that EasyOCR struggles with complex prescription layouts!
