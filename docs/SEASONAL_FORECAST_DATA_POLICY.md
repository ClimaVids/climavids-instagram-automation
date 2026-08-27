# Seasonal Forecast Data Policy

## Purpose

ClimaVids may publish an official forecast chart directly when the specific product is openly reusable for the intended use. The system should prefer the provider's original chart over rebuilding a visually equivalent map when the original chart is available and permitted.

## Approved-use rule

A chart is eligible only when its product/service has a verified reuse licence or explicit reuse terms compatible with the intended publication. The chart's provider, product, licence and retrieval metadata are stored with the content record.

## Attribution

Attribution is kept short in the social-media caption while the full source URL and provenance remain in the machine-readable content record. For ECMWF Open Data/Charts, the current project uses `Chart: ECMWF — CC BY 4.0` in the caption and retains the official chart URL in metadata. ECMWF's current guidance requires appropriate credit and identification of the dataset/service, source, licence and modifications where applicable. 

## Non-fabrication rule

The system must never infer forecast values from unrelated HTML prose, labels, page metadata or arbitrary numbers. When an official chart is the source, its image and provider metadata are the authoritative visual source; no pixel-to-number extraction is required for the post.

## Current implementation

The first production adapter is ECMWF Open Charts for SEAS5 precipitation. It retrieves the provider's original PNG URL through the OpenCharts API and records the forecast base month, valid month, area, forecast type, licence and attribution. ECMWF documents SEAS5 precipitation spatial maps and their forecast interpretation on the official chart product page.

NOAA CFSv2 and IRIMO remain separate source families and require product-specific licence verification before their charts are enabled for automated reuse.
