'''
Created on Jul 5, 2016

@author: lxh5147
'''

from keras import backend as K
from attention_layer import  HierarchicalAttention, ClassifierWithHierarchicalAttention

from keras.models import Model
import logging

logger = logging.getLogger(__name__)

def categorical_crossentropy_ex(y_true, y_pred):
    '''Expects a binary class matrix instead of a vector of scalar classes.
    '''
    return K.sum(K.categorical_crossentropy(y_pred, y_true))

def build_classifier_with_hierarchical_attention(input_shape, input_feature_dims, attention_output_dims, attention_weight_vector_dims, embedding_rows, embedding_dim, initial_embedding, use_sequence_to_vector_encoder, output_dim, hidden_unit_numbers, hidden_unit_activation_functions, output_activation_function='softmax'):
    inputs = HierarchicalAttention.build_inputs(input_shape, input_feature_dims)
    classifier = ClassifierWithHierarchicalAttention (input_feature_dims[0], attention_output_dims, attention_weight_vector_dims, embedding_rows, embedding_dim,
                 initial_embedding, use_sequence_to_vector_encoder, output_dim, hidden_unit_numbers, hidden_unit_activation_functions, output_activation_function)
    output = classifier(inputs)
    model = Model(input=inputs, output=output)
    return model
