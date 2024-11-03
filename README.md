# Quote Image Generator

![PyPI](https://img.shields.io/pypi/v/quote-image-generator)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/quote-image-generator)
![GitHub](https://img.shields.io/github/license/lordralinc/QIG)


**Create beautiful, customizable images with quotes, supporting unique font styles and emojis**


# Examples

[![base_quote](pics/base_quote.png)](examples/base_quote.py)
[![entities_quote](pics/entities_quote.png)](examples/entities_quote.py)

# Usage

## Emoji source

See `quote_image_generator.processors.emoji.ABCEmojiSource`

## Text processor

The `TextProcessor` class is designed for rendering text and entities.

See `quote_image_generator.text.TextProcessor`

## Entities processor

`EntitiesProcessor` is designed to process text entities, transforming them from the `InputEntity` type to DrawEntity with added styling, such as font and color.

# Pipelines

See `quote_image_generator.pipelines.base.BasePipeLine`

