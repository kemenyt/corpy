from collections import Counter
from collections.abc import Mapping, Iterable

import numpy as np
from wordcloud import WordCloud

CM_PER_IN = 2.54


def size_in_pixels(width, height, unit="in", ppi=300):
    """Convert size in inches/cm to pixels.

    width, height: dimensions, as measured by unit
    unit: "in" for inches, "cm" for centimeters
    ppi: pixels per inch

    Sample values for ppi:

    - for displays: you can detect your monitor's DPI using the
      following website:
      <https://www.infobyip.com/detectmonitordpi.php>; a typical
      value is 96 (of course, double that for HiDPI)
    - for print output: 300 at least, 600 is high quality

    """
    allowed_units = ("in", "cm")
    if unit not in allowed_units:
        raise ValueError(f"`unit` must be one of {allowed_units}.")
    if unit == "cm":
        width = round(width * CM_PER_IN)
        height = round(height * CM_PER_IN)
    return width * ppi, height * ppi


def _optimize_dimensions(size, fast, fast_limit):
    width, height = size
    # NOTE: Reasonable numbers for width and height are in the hundreds
    # to low thousands of pixels. If the requested size is large, for
    # faster results, we shrink the canvas during wordcloud
    # computation, and only scale it back up during rendering.
    if fast and width * height > fast_limit ** 2:
        scale = max(size) / fast_limit
        width = round(width / scale)
        height = round(height / scale)
    else:
        scale = 1
    return width, height, scale


def _elliptical_mask(width, height):
    x_center = half_width = round(width / 2)
    y_center = half_height = round(height / 2)
    x = np.arange(0, width)
    y = np.arange(0, height)[:, None]
    mat = ((x - x_center) / half_width) ** 2 + ((y - y_center) / half_height) ** 2
    return (mat >= 1) * 255


def wordcloud(
    data, size=(400, 400), *, rounded=False, fast=True, fast_limit=800, **kwargs
):
    """Generate a wordcloud.

    If `data` is a string, the wordcloud is generated using the
    method `.generate_from_text()`, which automatically ignores
    stopwords (customizable with the `stopwords` argument) and
    includes "collocations" (i.e. bigrams).

    If `data` is a sequence or a mapping, the wordcloud is generated
    using the method `.generate_from_frequencies()` and these
    preprocessing responsibilities fall to the user.

    data: input data -- either one long string of text, or an
        iterable of tokens, or a mapping of word types to their
        frequencies; use the second or third option if you want
        full control over the output
    size: size in pixels, as a tuple of integers, (width, height);
        if you want to specify the size in inches or cm, use the
        `size_in_pixels()` function to generate this tuple
    rounded: whether or not to enclose the wordcloud in an ellipse;
        incompatible with the `mask` keyword argument
    fast: when True, optimizes large wordclouds for speed of
        generation rather than precision of word placement
    fast_limit: speed optimizations for "large" wordclouds are
        applied when the requested canvas size is larger than
        `fast_limit**2`
    kwargs: remaining keyword arguments are passed on to the
        `wordcloud.WordCloud` initializer

    """
    if rounded and kwargs.get("mask"):
        raise ValueError("Can't specify `rounded` and `mask` at the same time.")
    # tweak defaults
    kwargs.setdefault("background_color", "white")
    # if Jupyter gets better at rendering transparent images, then
    # maybe these would be better defaults:
    # kwargs.setdefault("mode", "RGBA")
    # kwargs.setdefault("background_color", None)

    width, height, scale = _optimize_dimensions(size, fast, fast_limit)
    if rounded:
        kwargs["mask"] = _elliptical_mask(width, height)
    wc = WordCloud(width=width, height=height, scale=scale, **kwargs)

    # raw text
    if isinstance(data, str):
        return wc.generate_from_text(data)
    # frequency counts
    elif isinstance(data, Mapping):
        return wc.generate_from_frequencies(data)
    # tokenized text
    # NOTE: the second condition is there because of nltk.text, which
    # behaves like an Iterable / Collection / Sequence for all
    # practical intents and purposes, but the corresponding abstract
    # base classes don't pick up on it (maybe because it only has a
    # __getitem__ magic method?)
    elif isinstance(data, Iterable) or hasattr(data, "__getitem__"):
        return wc.generate_from_frequencies(Counter(data))
    else:
        raise ValueError(
            "`data` must be a string, a mapping from words to frequencies, or an iterable of words."
        )


def _wordcloud_png(wc):
    from IPython.display import display

    return display(wc.to_image())


try:
    from IPython import get_ipython

    ip = get_ipython()
    if ip is not None:
        png_formatter = ip.display_formatter.formatters["image/png"]
        png_formatter.for_type(WordCloud, _wordcloud_png)
except ImportError:
    pass
