from skimage.feature import canny
from skimage.filters import scharr
from skimage import exposure
from skimage.color import rgb2gray
from skimage.io import imread
from keras_preprocessing.image import ImageDataGenerator
import numpy as np


DATA_FOLDER = "../data/"
TEST_DATA = DATA_FOLDER + "images/test/"
TRAIN_DATA = DATA_FOLDER + "images/train/"


def apply_filter(img, name="equalizer"):
    """
        applying filter to the input image
    :param img:  input image
    :param name: requested filter
    :return:  image after applying the filter
    """
    if name == "equalizer":
        return exposure.equalize_hist(img)
    elif name == "adaptive_equalization":
        return exposure.equalize_adapthist(img)
    elif name == "sobel_op":
        return scharr(img, )
    elif name == "canny_feature":
        return canny(rgb2gray(img), sigma=4)
    else:
        return exposure.equalize_hist(img)


def rle_decode(mask_rle, shape=(768, 768)):
    """
    mask_rle: run-length as string formated (start length)
    shape: (height,width) of array to return
    Returns numpy array, 1 - mask, 0 - background
    """

    s = mask_rle.split()
    starts, lengths = [np.asarray(x, dtype=int) for x in (s[0:][::2], s[1:][::2])]
    starts -= 1
    ends = starts + lengths
    img = np.zeros(shape[0] * shape[1], dtype=np.uint8)
    for lo, hi in zip(starts, ends):
        img[lo:hi] = 1
    return img.reshape(shape).T


def rle_encode(img):
    """
    img: numpy array, 1 - mask, 0 - background
    Returns run length as string formated
    """
    pixels = img.T.flatten()
    pixels = np.concatenate([[0], pixels, [0]])
    runs = np.where(pixels[1:] != pixels[:-1])[0] + 1
    runs[1::2] -= runs[::2]
    return ' '.join(str(x) for x in runs)


def masks_as_image(in_mask_list):
    """
    Combine masks into one image
    :param in_mask_list:  a list of masks in the form of RLE
    :return: an array containing the masks (can be represented as an image)
    """
    all_masks = np.zeros((768, 768), dtype=np.int16)
    for mask in in_mask_list:
        if isinstance(mask, str):
            all_masks += rle_decode(mask)
    return np.expand_dims(all_masks, -1)


def get_augmented_images_generator(in_gen, seed=None):
    """
    Augmented data generator
    :param in_gen: image loader generator
    :param seed: a random seed
    :return: an image generator
    """
    dg_args = dict(featurewise_center=False,
                   samplewise_center=False,
                   rotation_range=15,
                   width_shift_range=0.1,
                   height_shift_range=0.1,
                   shear_range=0.01,
                   zoom_range=[0.9, 1.25],
                   horizontal_flip=True,
                   vertical_flip=True,
                   fill_mode='reflect',
                   data_format='channels_last')
    image_gen = ImageDataGenerator(**dg_args)
    label_gen = ImageDataGenerator(**dg_args)

    np.random.seed(seed if seed is not None else np.random.choice(range(9999)))
    for in_x, in_y in in_gen:
        seed = np.random.choice(range(9999))
        # keep the seeds synchronized otherwise the augmentation to the images is different from the masks
        g_x = image_gen.flow(255 * in_x,
                             batch_size=in_x.shape[0],
                             seed=seed,
                             shuffle=True)
        g_y = label_gen.flow(in_y,
                             batch_size=in_x.shape[0],
                             seed=seed,
                             shuffle=True)

        yield next(g_x) / 255.0, next(g_y)


def get_colors_for_class_ids(class_ids):
    """
    assign a class with a color
    """
    colors = []
    for class_id in class_ids:
        if class_id == 1:
            colors.append((.941, .204, .204))
    return colors


def get_image(img_id, from_train=True):
    """
    load the requested image
    :param img_id:  the id of the image, which is also its filename
    :param from_train: from training set else from testing
    :return: the image
    """
    if from_train:
        return imread(TRAIN_DATA + img_id)
    else:
        return imread(TEST_DATA + img_id)
