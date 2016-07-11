'''
Created on Jul 5, 2016

@author: lxh5147
'''

from keras import backend as K
from keras.layers.embeddings import Embedding
from keras.layers import Input
from keras.layers import Dense, Dropout, Activation
from keras.layers.wrappers import TimeDistributed
from attention_layer import check_and_throw_if_fail, apply_attention_layer_with_sequence_to_sequence_encoder 
from keras.models import Model
import logging

logger = logging.getLogger(__name__)

def build_hierarchical_attention_layers(input_shape, input_feature_dims, output_dims, attention_weight_vector_dims, vocabulary_size, word_embedding_dim, initial_embedding):
    '''
    input_shape: batch_size * time_steps* document * section* sentence * word
    input_feature_dims: [cacdi_snapshot_input_feature_dim, document_input_feature_dim,section_input_feature_dim,sentence_input_feature_dim,word_input_feature_dim]
    output_dims: [cacdi_snapshot_output_dim, document_output_dim,section_output_dim,sentence_output_dim]
    attention_weight_vector_dims: [cacdi_snapshot_weight_vector_dim,document_weight_vector_dim,section_weight_vector_dim,sentence_weight_vector_dim]
    '''
    inputs = []
    check_and_throw_if_fail(len(input_shape) >= 3 , "input_shape")
    check_and_throw_if_fail(len(input_feature_dims) == len(input_shape) - 1 , "input_feature_dims")
    check_and_throw_if_fail(len(output_dims) == len(input_shape) - 2 , "output_dims")
    check_and_throw_if_fail(len(attention_weight_vector_dims) == len(output_dims), "attention_weight_vector_dims")
    total_dim = len(input_shape)
    embedding = Embedding(vocabulary_size, word_embedding_dim, weights = initial_embedding)
    cur_input = Input(shape = input_shape)
    inputs.append(cur_input)
    # reshape to 2D
    cur_input = K.reshape(cur_input, (-1, input_shape[-1]))
    cur_input = embedding(cur_input)
    # embedding increases dimension 
    cur_input = K.reshape(input_shape + [word_embedding_dim])
    for cur_dim in xrange(total_dim - 1 , 1, -1):
        input_feature = Input(shape = input_shape[:cur_dim + 1] + [input_feature_dims[cur_dim - 1]])
        inputs.append(input_feature)
        cur_input = K.concatenate([cur_input, input_feature], axis = -1)
        cur_input_shape = K.shape(cur_input)
        cur_input = K.reshape(cur_input, (-1, cur_input_shape[-2], cur_input_shape[-1]))
        cur_output_dim = output_dims[cur_dim - 2]
        cur_input = apply_attention_layer_with_sequence_to_sequence_encoder(cur_input, cur_output_dim, attention_weight_vector_dim = attention_weight_vector_dims[cur_dim - 2])
        cur_input = K.reshape(cur_input_shape[:-2] + [cur_output_dim])

    input_feature = Input(shape = input_shape[:2] + [input_feature_dims[0]])
    # cur_input: batch_size*time_steps*cacdi_snapshot_attention
    cur_input = K.concatenate([cur_input, input_feature], axis = -1)
    return inputs, cur_input

def apply_mlp_softmax_classifier(input_sequence, output_dim, hidden_unit_numbers, drop_out_rates):
    '''
    input_sequence: input sequence, batch_size * time_steps * input_dim
    hidden_unit_numbers: number of hidden units of each hidden layer
    drop_out_rates: drop out rates of each hidden layer
    output_dim: output dimension
    '''
    check_and_throw_if_fail(K.ndim(input_sequence) == 3 , "input_sequence")
    output = input_sequence
    for hidden_unit_number, drop_out_rate in zip([hidden_unit_numbers, drop_out_rates]):
        output = TimeDistributed(Dense(hidden_unit_number, init = 'uniform'))(input_sequence)
        output = TimeDistributed(Activation('tanh'))(output)
        output = TimeDistributed(Dropout(drop_out_rate))(output)
    output = TimeDistributed(Dense(output_dim, init = 'uniform'))(output)
    output = TimeDistributed(Activation('softmax'))(output)
    return K.reshape(output, (-1, output_dim))

def build_hierarchical_attention_model(input_shape, input_feature_dims, output_dims, attention_weight_vector_dims, vocabulary_size, word_embedding_dim, initial_embedding, output_dim, hidden_unit_numbers, drop_out_rates):
    inputs, cur_input = build_hierarchical_attention_layers(input_shape, input_feature_dims, output_dims, attention_weight_vector_dims, vocabulary_size, word_embedding_dim, initial_embedding)
    output = apply_mlp_softmax_classifier(cur_input, output_dim, hidden_unit_numbers, drop_out_rates)
    model = Model(input = inputs, output = output)
    return model