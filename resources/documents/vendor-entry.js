import { marked } from 'marked';
import DOMPurify from 'dompurify';
import mermaid from 'mermaid';
import { parse as losslessParse, stringify as losslessStringify } from 'lossless-json';
window.docVendor = { marked, DOMPurify, mermaid, losslessParse, losslessStringify };
