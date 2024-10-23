# ComfyUI Together.ai FLUX API Node Usage Guide

## Setup

1. Ensure you have a Together.ai account and API key
2. Configure your API key in `config.ini`
3. Install all required dependencies

## Node Configuration

### Input Parameters

#### Required Parameters:
- **Prompt** (String)
  - Your main generation prompt
  - Supports multiline input
  - Be specific and detailed for best results

- **Negative Prompt** (String)
  - Elements you want to avoid in the generation
  - Supports multiline input
  - Leave empty if not needed

- **Steps** (Integer)
  - Range: 1-100
  - Default: 20
  - Higher values generally produce better quality but take longer
  - Recommended range: 20-50 for most use cases

- **Width** (Integer)
  - Range: 512-2048
  - Default: 1024
  - Must be a multiple of 8
  - Common values: 512, 768, 1024

- **Height** (Integer)
  - Range: 512-2048
  - Default: 1024
  - Must be a multiple of 8
  - Common values: 512, 768, 1024

- **Seed** (Integer)
  - Range: 0 to max 64-bit integer
  - Default: 0
  - Use specific seeds to reproduce results
  - 0 or -1 for random seed

- **CFG (Guidance Scale)** (Float)
  - Range: 0.0-20.0
  - Default: 7.0
  - Controls how closely the image follows the prompt
  - Recommended range: 5.0-10.0

### Output

The node outputs a single image tensor compatible with other ComfyUI nodes.

## Best Practices

1. **Prompt Engineering**
   - Be specific and detailed in your prompts
   - Use descriptive adjectives
   - Include style references when needed

2. **Performance**
   - Start with lower step counts (20-30) for testing
   - Increase steps for final generations
   - Use reasonable image dimensions (1024x1024 is standard)

3. **Error Handling**
   - Check console for error messages
   - Verify API key is correctly configured
   - Ensure parameters are within valid ranges

## Common Workflows

### Basic Image Generation
1. Add Together API Node to workspace
2. Connect to a Load Image node
3. Configure prompt and basic parameters
4. Execute workflow

### Advanced Usage
1. Combine with other ComfyUI nodes
2. Use seed control for consistent results
3. Experiment with guidance scale for style control

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify key in config.ini
   - Check API key validity
   - Ensure proper formatting

2. **Generation Errors**
   - Verify parameter ranges
   - Check prompt length
   - Monitor API rate limits

3. **Image Quality Issues**
   - Adjust step count
   - Modify guidance scale
   - Refine prompt

## Examples

### Basic Prompt Example
```
A beautiful landscape with mountains and lakes, cinematic lighting, high detail
```

### Advanced Prompt Example
```
A stunning mountain landscape at sunset, volumetric lighting, 
golden hour, ultra detailed, professional photography, 
8k resolution, artistic composition
```

### Negative Prompt Example
```
blur, haze, low quality, distortion, bad composition, 
oversaturated, unrealistic lighting
```

## Support

For issues and feature requests, please use the GitHub issue tracker.
