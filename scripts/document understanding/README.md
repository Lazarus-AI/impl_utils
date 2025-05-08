# Document Understanding

## The Origins
This project began in response to the performance of Rick* on the following (synthetically-filled) form for a potential customer:

![Lexis Nexis example](example_images/infill_demo2.jpg)

The accuracy issues were said to be common to forms with similarly complex layouts and boxes with numeric 'labels' (see the side 'rails').

## The Idea
We formed the hypothesis that with minimal pre-processing we could augment OCR with structural information about the layout of the form and improve model accuracy.
This yielded a number of project directions:
* create an xml-style format for complex layouts which matches the logical breakdown that a human sees
* create a prompting method that directs the model more explicitly and successfully to content in the form (Rick* fails to recognize "Box 96", for example)
* create a workflow that performs simple extraction using a model light enough to handle each extraction independently (Rick* is too expensive/slow to use one call per extracted value, but the accuracy suffers when all extraction tasks are lumped together for one document)
* create a lightweight machine-text-only ocr that can handle single character text as seen in character-by-character inputs like VIN (Lazarus OCRv2 fails to read this text correctly)

## Bonus Points
Early experiments in the document understanding workflow had an unexpected benefit: the input fields of blank forms could be automatically identified and labeled, allowing synthetic data to be generated. This allows model evaluations early in the customer sales pipeline.

# Basic Pipeline
Using opencv we:
* find all connected components in the binarized image
* filter out those small enough to be characters
* filter the remaining pixels to find vertical /horizontal lines
* find distinct bounded regions of this 'structure' (see below)
![Structure Example](example_images/structure_image.jpg)

We can now explicitly label the bounded regions (Cells) and associate the label with the contained content:

```python
cell_id = 2
cell_data = cell_components.components[cell_id]
cell_mask = cell_components.mask[cell_data['top']:cell_data['bottom'], cell_data['left']:cell_data['right']]
cell_window = 255 - binary_image[cell_data['top']:cell_data['bottom'], cell_data['left']:cell_data['right']]
cell_image = np.where(cell_mask == cell_id, cell_window, 255).astype('uint8')
cv2.imwrite('example_images/cell_2_image.jpg', cell_image)
```
The snippet above yields:

![Structure Example](example_images/cell_2_image.jpg)

Which we might naively encode with text alignment as
```commandline
<cell_2><upper_left>'96'</upper_left><bottom_center>'02'</bottom_center></cell_2>
```

We may then ask a SLM to perform the extraction for this content:
```python
import outlines
from outlines.samplers import greedy


model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct", device="cuda")
generator = outlines.generate.text(model, sampler=greedy())


system_prompt = '<instructions>A user has entered data into a form. EXTRACT values verbatim from the form (IGNORE the form question and return only the value provided by the user).</instructions>\n\n'
form_excerpt = "<form><cell_2><upper_left>'96'</upper_left><bottom_center>'02'</bottom_center></cell_2></form>\n\n"

generator(f'{system_prompt}{form_excerpt}<request>EXTRACT the value provided by the user in cell 2 associated with the label "96"</request>\n\n<response>',
          max_tokens=100,
          stop_at='</response>'
          )
          
>>> '02</response>'
```
Note that without the hint as to what was the key and what was the value yields a wrong answer:
```python
generator(f'{system_prompt}{form_excerpt}<request>EXTRACT the value provided by the user in cell 2.</request>\n\n<response>',
          max_tokens=100,
          stop_at='</response>'
          )
          
>>> '9602</response>'
```
This suggest that either 
* prompt engineers will need to craft prompts knowing the format in advance (templating), or
* work will have to be done to distinguish form keys from user input

It seems likely that simple formatting heuristics will go far, but more sophisticated / multi-round prompting may be needed.
Revising the system prompt worked in this specific instance:
```python
system_prompt = '<instructions>A user has entered data into a form. EXTRACT values verbatim from the form (IGNORE the form question and return only the value provided by the user). Within a cell, text in the "upper_left" is typically part of the form, whereas text in the "bottom_center" is typically user content.</instructions>\n\n'
```
